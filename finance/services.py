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
        first_day = date(self.year, self.month, 1)
        last_day = date(
            self.year,
            self.month,
            calendar.monthrange(self.year, self.month)[1],
        )
        users = list(
            User.objects.filter(is_active=True).order_by(Lower('username'), 'pk')
        )
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

        expenses = (
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
        for expense in expenses:
            if expense.all_participants:
                participants = [
                    participant
                    for participant in expense.all_participants
                    if participant.is_active
                ]
            else:
                participants = users

            if not participants:
                continue

            total_spent += expense.amount
            spent_by_user[expense.user_id] += expense.amount
            total_cents = int(expense.amount / CENT)
            base_share_cents, remainder_cents = divmod(
                total_cents,
                len(participants),
            )
            for index, participant in enumerate(participants):
                share_cents = base_share_cents + (index < remainder_cents)
                share_by_user[participant.pk] += Decimal(share_cents) * CENT

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
