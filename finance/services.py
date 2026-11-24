import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Prefetch, Sum
from django.db.models.functions import Lower

from finance.models import Expense, User


CENT = Decimal('0.01')


@dataclass(frozen=True)
class UserMonthlyBalance:
    spent: Decimal
    share: Decimal
    balance: Decimal


@dataclass(frozen=True)
class DailyUserAmounts:
    paid: Decimal
    share: Decimal


@dataclass(frozen=True)
class MonthlyFinanceResult:
    year: int
    month: int
    total_spent: Decimal
    active_user_count: int
    balances: dict[int, UserMonthlyBalance]


class Finance:
    def __init__(self, year, month):
        date(year, month, 1)
        self.year = year
        self.month = month

    def calculate(self):
        users = self._active_users()
        user_ids = [user.pk for user in users]
        spent_by_user = {user_id: Decimal('0.00') for user_id in user_ids}
        share_by_user = {user_id: Decimal('0.00') for user_id in user_ids}
        total_spent = Decimal('0.00')

        if not users:
            return MonthlyFinanceResult(
                year=self.year,
                month=self.month,
                total_spent=total_spent,
                active_user_count=0,
                balances={},
            )

        for expense in self._month_expenses(user_ids):
            participants = self._participants_for_expense(expense, users)
            shares = self._shares_for_expense(expense, participants)
            if not shares:
                continue

            total_spent += expense.amount
            spent_by_user[expense.user_id] += expense.amount
            for user_id, share in shares.items():
                share_by_user[user_id] += share

        balances = {}
        for user_id in user_ids:
            spent = spent_by_user[user_id]
            share = share_by_user[user_id]
            balances[user_id] = UserMonthlyBalance(
                spent=spent,
                share=share,
                balance=spent - share,
            )

        return MonthlyFinanceResult(
            year=self.year,
            month=self.month,
            total_spent=total_spent,
            active_user_count=len(users),
            balances=balances,
        )

    def calculate_user_daily_amounts(self, user_id):
        users = self._active_users()
        user_ids = [user.pk for user in users]
        zero = Decimal('0.00')
        daily_amounts = {
            date(self.year, self.month, day): DailyUserAmounts(paid=zero, share=zero)
            for day in range(
                1,
                calendar.monthrange(self.year, self.month)[1] + 1,
            )
        }
        if user_id not in user_ids:
            return daily_amounts

        for expense in self._month_expenses(user_ids):
            participants = self._participants_for_expense(expense, users)
            shares = self._shares_for_expense(expense, participants)
            if not shares:
                continue

            current = daily_amounts[expense.occurred_on]
            daily_amounts[expense.occurred_on] = DailyUserAmounts(
                paid=current.paid
                + (expense.amount if expense.user_id == user_id else zero),
                share=current.share + shares.get(user_id, zero),
            )

        return daily_amounts

    def _active_users(self):
        return list(
            User.objects.filter(is_active=True).order_by(Lower('username'), 'pk')
        )

    def _month_expenses(self, user_ids):
        first_day = date(self.year, self.month, 1)
        last_day = date(
            self.year,
            self.month,
            calendar.monthrange(self.year, self.month)[1],
        )
        return (
            Expense.objects.filter(
                is_active=True,
                user_id__in=user_ids,
                occurred_on__range=(first_day, last_day),
            )
            .select_related('user')
            .prefetch_related(
                Prefetch(
                    'participants',
                    queryset=User.objects.order_by(Lower('username'), 'pk'),
                    to_attr='all_participants',
                )
            )
            .order_by('pk')
        )

    @staticmethod
    def _participants_for_expense(expense, active_users):
        if expense.all_participants:
            return [
                participant
                for participant in expense.all_participants
                if participant.is_active
            ]
        return active_users

    @staticmethod
    def _shares_for_expense(expense, participants):
        if not participants:
            return {}

        total_cents = int(expense.amount / CENT)
        base_share_cents, remainder_cents = divmod(
            total_cents,
            len(participants),
        )
        return {
            participant.pk: Decimal(
                base_share_cents + (index < remainder_cents)
            )
            * CENT
            for index, participant in enumerate(participants)
        }
