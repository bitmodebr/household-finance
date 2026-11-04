from datetime import date, datetime, timezone as datetime_timezone
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from finance.models import Expense, User
from finance.services import Finance


class MonthlyFinanceTests(TestCase):
    def create_member(self, username, email):
        return User.objects.create_user(
            username=username,
            email=email,
            first_name=username,
            password='StrongPass123!',
        )

    def add_expense(self, user, amount, occurred_on, participants=None):
        expense = Expense.objects.create(
            creator=user,
            user=user,
            amount=Decimal(amount),
            occurred_on=date.fromisoformat(occurred_on),
        )
        if participants is not None:
            expense.participants.set(participants)
        return expense

    def setUp(self):
        self.ana = self.create_member('ana', 'ana@example.com')
        self.bia = self.create_member('bia', 'bia@example.com')
        self.caio = self.create_member('caio', 'caio@example.com')

    def test_calculates_only_expenses_inclusive_of_calendar_month_boundaries(self):
        self.add_expense(self.ana, '10.00', '2024-01-01')
        self.add_expense(self.bia, '20.00', '2024-01-31')
        self.add_expense(self.ana, '900.00', '2023-12-31')
        self.add_expense(self.bia, '800.00', '2024-02-01')

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.total_spent, Decimal('30.00'))
        self.assertEqual(result.active_user_count, 3)
        self.assertEqual(result.balances[self.ana.pk].spent, Decimal('10.00'))
        self.assertEqual(result.balances[self.bia.pk].spent, Decimal('20.00'))
        self.assertEqual(result.balances[self.caio.pk].spent, Decimal('0.00'))

    def test_inactive_users_expenses_do_not_participate_in_the_monthly_total(self):
        self.caio.is_active = False
        self.caio.save(update_fields=['is_active'])
        self.add_expense(self.ana, '30.00', '2024-01-15')
        self.add_expense(self.caio, '70.00', '2024-01-15')

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.total_spent, Decimal('30.00'))
        self.assertEqual(result.active_user_count, 2)
        self.assertNotIn(self.caio.pk, result.balances)
        self.assertEqual(result.balances[self.ana.pk].share, Decimal('15.00'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('15.00'))

    def test_user_without_expenses_is_included_in_equal_split(self):
        self.add_expense(self.ana, '30.00', '2024-01-15')

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.active_user_count, 3)
        self.assertEqual(result.balances[self.caio.pk].spent, Decimal('0.00'))
        self.assertEqual(result.balances[self.caio.pk].share, Decimal('10.00'))
        self.assertEqual(result.balances[self.caio.pk].balance, Decimal('-10.00'))

    def test_cent_remainders_are_assigned_in_username_order(self):
        self.add_expense(self.ana, '100.01', '2024-01-15')

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.balances[self.ana.pk].share, Decimal('33.34'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('33.34'))
        self.assertEqual(result.balances[self.caio.pk].share, Decimal('33.33'))
        self.assertEqual(
            sum((balance.share for balance in result.balances.values()), Decimal('0.00')),
            result.total_spent,
        )
        self.assertEqual(
            sum(
                (balance.balance for balance in result.balances.values()),
                Decimal('0.00'),
            ),
            Decimal('0.00'),
        )

    def test_february_uses_the_last_calendar_day_in_a_leap_year(self):
        self.add_expense(self.ana, '10.00', '2024-02-29')
        self.add_expense(self.bia, '100.00', '2024-03-01')

        result = Finance(2024, 2).calculate()

        self.assertEqual(result.total_spent, Decimal('10.00'))
        self.assertEqual(result.balances[self.ana.pk].spent, Decimal('10.00'))

    def test_no_active_users_produces_an_empty_result(self):
        User.objects.update(is_active=False)
        self.add_expense(self.ana, '10.00', '2024-01-15')

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.total_spent, Decimal('0.00'))
        self.assertEqual(result.active_user_count, 0)
        self.assertEqual(result.balances, {})

    def test_month_must_be_valid(self):
        with self.assertRaises(ValueError):
            Finance(2024, 13)

    @patch(
        'django.utils.timezone.now',
        return_value=datetime(2024, 1, 15, 14, 32, 45, tzinfo=datetime_timezone.utc),
    )
    def test_expense_creation_records_timestamp_in_sao_paulo_timezone(self, mocked_now):
        expense = self.add_expense(self.ana, '10.00', '2024-01-15')
        created_at = timezone.localtime(expense.created_at)

        self.assertTrue(timezone.is_aware(expense.created_at))
        self.assertEqual(created_at.year, 2024)
        self.assertEqual(created_at.month, 1)
        self.assertEqual(created_at.day, 15)
        self.assertEqual(created_at.hour, 11)
        self.assertEqual(created_at.minute, 32)
        self.assertEqual(created_at.second, 45)
        mocked_now.assert_called_once()

    def test_expense_is_active_by_default(self):
        expense = self.add_expense(self.ana, '10.00', '2024-01-15')

        self.assertTrue(expense.is_active)

    def test_deleting_expense_marks_it_inactive_without_removing_it(self):
        expense = self.add_expense(self.ana, '30.00', '2024-01-15')

        expense.delete()

        expense.refresh_from_db()
        self.assertFalse(expense.is_active)
        self.assertTrue(Expense.objects.filter(pk=expense.pk).exists())

    def test_bulk_delete_marks_expenses_inactive_without_removing_them(self):
        expenses = [
            self.add_expense(self.ana, '10.00', '2024-01-15'),
            self.add_expense(self.bia, '20.00', '2024-01-16'),
        ]

        deleted_count, _ = Expense.objects.filter(pk__in=[
            expense.pk for expense in expenses
        ]).delete()

        self.assertEqual(deleted_count, 2)
        self.assertEqual(
            Expense.objects.filter(pk__in=[expense.pk for expense in expenses]).count(),
            2,
        )
        self.assertFalse(
            Expense.objects.filter(
                pk__in=[expense.pk for expense in expenses],
                is_active=True,
            ).exists()
        )

    def test_inactive_expense_is_excluded_from_monthly_calculation(self):
        expense = self.add_expense(self.ana, '90.00', '2024-01-15')
        self.add_expense(self.bia, '30.00', '2024-01-16')
        expense.delete()

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.total_spent, Decimal('30.00'))
        self.assertEqual(result.balances[self.ana.pk].spent, Decimal('0.00'))
        self.assertEqual(result.balances[self.bia.pk].spent, Decimal('30.00'))

    def test_expense_can_be_split_between_exactly_two_active_users(self):
        self.add_expense(
            self.ana,
            '90.00',
            '2024-01-15',
            participants=[self.ana, self.bia],
        )

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.total_spent, Decimal('90.00'))
        self.assertEqual(result.balances[self.ana.pk].share, Decimal('45.00'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('45.00'))
        self.assertEqual(result.balances[self.caio.pk].share, Decimal('0.00'))

    def test_expense_can_be_split_between_exactly_three_active_users(self):
        self.add_expense(
            self.ana,
            '90.00',
            '2024-01-15',
            participants=[self.ana, self.bia, self.caio],
        )

        result = Finance(2024, 1).calculate()

        for user in (self.ana, self.bia, self.caio):
            self.assertEqual(result.balances[user.pk].share, Decimal('30.00'))

    def test_expense_can_be_split_among_four_active_users(self):
        davi = self.create_member('davi', 'davi@example.com')
        self.add_expense(
            self.ana,
            '100.00',
            '2024-01-15',
            participants=[self.ana, self.bia, self.caio, davi],
        )

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.active_user_count, 4)
        for user in (self.ana, self.bia, self.caio, davi):
            self.assertEqual(result.balances[user.pk].share, Decimal('25.00'))

    def test_expense_can_be_assigned_to_only_one_active_user(self):
        self.add_expense(
            self.ana,
            '90.00',
            '2024-01-15',
            participants=[self.ana],
        )

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.balances[self.ana.pk].share, Decimal('90.00'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('0.00'))
        self.assertEqual(result.balances[self.caio.pk].share, Decimal('0.00'))
        self.assertEqual(result.balances[self.ana.pk].balance, Decimal('0.00'))

    def test_each_expense_can_have_a_different_participant_group(self):
        self.add_expense(
            self.ana,
            '90.00',
            '2024-01-15',
            participants=[self.ana, self.bia],
        )
        self.add_expense(
            self.caio,
            '60.00',
            '2024-01-16',
            participants=[self.caio],
        )

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.total_spent, Decimal('150.00'))
        self.assertEqual(result.balances[self.ana.pk].spent, Decimal('90.00'))
        self.assertEqual(result.balances[self.ana.pk].share, Decimal('45.00'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('45.00'))
        self.assertEqual(result.balances[self.caio.pk].share, Decimal('60.00'))

    def test_expense_without_explicit_participants_uses_all_active_users(self):
        self.add_expense(self.ana, '90.00', '2024-01-15')

        result = Finance(2024, 1).calculate()

        for user in (self.ana, self.bia, self.caio):
            self.assertEqual(result.balances[user.pk].share, Decimal('30.00'))

    def test_inactive_explicit_participants_are_not_included_in_the_split(self):
        self.caio.is_active = False
        self.caio.save(update_fields=['is_active'])
        self.add_expense(
            self.ana,
            '90.00',
            '2024-01-15',
            participants=[self.ana, self.bia, self.caio],
        )

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.active_user_count, 2)
        self.assertEqual(result.balances[self.ana.pk].share, Decimal('45.00'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('45.00'))
        self.assertNotIn(self.caio.pk, result.balances)

    def test_cent_remainder_is_distributed_within_expense_participants(self):
        self.add_expense(
            self.ana,
            '10.00',
            '2024-01-15',
            participants=[self.ana, self.bia],
        )
        self.add_expense(
            self.caio,
            '10.00',
            '2024-01-16',
            participants=[self.bia, self.caio],
        )

        result = Finance(2024, 1).calculate()

        self.assertEqual(result.balances[self.ana.pk].share, Decimal('5.00'))
        self.assertEqual(result.balances[self.bia.pk].share, Decimal('10.00'))
        self.assertEqual(result.balances[self.caio.pk].share, Decimal('5.00'))
