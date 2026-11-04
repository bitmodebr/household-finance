from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from finance.admin import ExpenseAdmin, UserAdmin
from finance.models import Expense, User


class FinanceAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='rootadmin',
            email='root@example.com',
            password='StrongAdmin123!',
        )
        self.user = User.objects.create_user(
            username='ana',
            email='ana@example.com',
            first_name='Ana',
            password='StrongPass123!',
        )
        self.expense = Expense.objects.create(
            creator=self.admin_user,
            user=self.user,
            amount=Decimal('25.00'),
            occurred_on=date(2024, 1, 15),
        )
        self.client.force_login(self.admin_user)

    def test_user_and_expense_models_are_registered_in_admin(self):
        self.assertIsInstance(admin.site._registry[User], UserAdmin)
        self.assertIsInstance(admin.site._registry[Expense], ExpenseAdmin)

    def test_superuser_can_open_user_admin_pages(self):
        changelist = self.client.get(reverse('admin:finance_user_changelist'))
        add_form = self.client.get(reverse('admin:finance_user_add'))
        change_form = self.client.get(
            reverse('admin:finance_user_change', args=[self.user.pk])
        )

        self.assertEqual(changelist.status_code, 200)
        self.assertEqual(add_form.status_code, 200)
        self.assertEqual(change_form.status_code, 200)

    def test_superuser_can_create_user_in_admin(self):
        response = self.client.post(
            reverse('admin:finance_user_add'),
            {
                'username': 'novousuario',
                'password1': 'StrongNewPass123!',
                'password2': 'StrongNewPass123!',
                'cpf': '',
                '_save': 'Save',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='novousuario').exists())

    def test_superuser_can_open_expense_admin_pages(self):
        changelist = self.client.get(reverse('admin:finance_expense_changelist'))
        add_form = self.client.get(reverse('admin:finance_expense_add'))
        change_form = self.client.get(
            reverse('admin:finance_expense_change', args=[self.expense.pk])
        )

        self.assertEqual(changelist.status_code, 200)
        self.assertEqual(add_form.status_code, 200)
        self.assertEqual(change_form.status_code, 200)

    def test_superuser_can_create_expense_in_admin(self):
        response = self.client.post(
            reverse('admin:finance_expense_add'),
            {
                'user': self.user.pk,
                'amount': '40.00',
                'occurred_on': '2024-01-20',
                'is_active': 'on',
                'creator': self.user.pk,
                'participants': [],
                '_save': 'Save',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Expense.objects.filter(
                user=self.user,
                amount=Decimal('40.00'),
                occurred_on=date(2024, 1, 20),
                creator=self.admin_user,
            ).exists()
        )

    def test_expense_creator_is_read_only_in_admin(self):
        self.assertIn('creator', ExpenseAdmin.readonly_fields)

    def test_expense_creator_cannot_be_changed_through_model_save(self):
        self.expense.creator = self.user

        with self.assertRaises(ValidationError):
            self.expense.save()

        self.expense.refresh_from_db()
        self.assertEqual(self.expense.creator, self.admin_user)

    def test_expense_creator_cannot_be_changed_through_queryset_update(self):
        with self.assertRaises(ValidationError):
            Expense.objects.filter(pk=self.expense.pk).update(creator=self.user)

    def test_admin_cannot_change_existing_expense_creator(self):
        response = self.client.post(
            reverse('admin:finance_expense_change', args=[self.expense.pk]),
            {
                'creator': self.user.pk,
                'user': self.user.pk,
                'amount': '25.00',
                'occurred_on': '2024-01-15',
                'is_active': 'on',
                'participants': [],
                '_save': 'Save',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.creator, self.admin_user)

    def test_admin_delete_keeps_expense_and_marks_it_inactive(self):
        response = self.client.post(
            reverse('admin:finance_expense_delete', args=[self.expense.pk]),
            {'post': 'yes'},
        )

        self.assertEqual(response.status_code, 302)
        self.expense.refresh_from_db()
        self.assertFalse(self.expense.is_active)
        self.assertTrue(Expense.objects.filter(pk=self.expense.pk).exists())
