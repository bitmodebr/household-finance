from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from finance.models import Expense, PaymentMethod, User


class EditPaymentViewTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            first_name='Maria',
            password='SecurePassword123!',
        )
        self.other_user = User.objects.create_user(
            username='ana',
            email='ana@example.com',
            first_name='Ana',
            password='SecurePassword123!',
        )
        self.expense = Expense.objects.create(
            title='Conta original',
            description='Descrição original',
            payment_method=PaymentMethod.PIX,
            creator=self.creator,
            user=self.other_user,
            amount=Decimal('25.00'),
            occurred_on=date(2026, 11, 5),
        )
        self.expense.participants.set([self.creator])

    def payment_data(self, **overrides):
        data = {
            'title': 'Conta atualizada',
            'description': 'Descrição atualizada',
            'payment_method': PaymentMethod.CREDIT_CARD,
            'creator': str(self.other_user.pk),
            'user': str(self.creator.pk),
            'amount': '75.50',
            'occurred_on': '2026-11-06',
            'participants': [str(self.other_user.pk)],
            'updated_at': '2000-01-01T00:00',
        }
        data.update(overrides)
        return data

    def test_anonymous_user_cannot_open_or_submit_payment_edits(self):
        response = self.client.get(
            reverse('edit_payment', args=[self.expense.pk])
        )

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("edit_payment", args=[self.expense.pk])}',
        )
        response = self.client.post(
            reverse('edit_payment', args=[self.expense.pk]),
            self.payment_data(),
        )

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("edit_payment", args=[self.expense.pk])}',
        )
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.title, 'Conta original')
        self.assertEqual(self.expense.amount, Decimal('25.00'))

    def test_only_creator_can_open_or_submit_payment_edits(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse('edit_payment', args=[self.expense.pk])
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse('edit_payment', args=[self.expense.pk]),
            self.payment_data(),
        )
        self.assertEqual(response.status_code, 404)

        self.expense.refresh_from_db()
        self.assertEqual(self.expense.title, 'Conta original')
        self.assertEqual(self.expense.amount, Decimal('25.00'))
        self.assertSetEqual(
            set(self.expense.participants.values_list('pk', flat=True)),
            {self.creator.pk},
        )

    def test_creator_can_update_payment_and_updated_at_is_server_managed(self):
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse('edit_payment', args=[self.expense.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, self.expense)
        self.assertNotIn('creator', response.context['form'].fields)
        self.assertNotIn('updated_at', response.context['form'].fields)

        updated_at = timezone.now() + timedelta(minutes=1)
        with patch('django.utils.timezone.now', return_value=updated_at):
            response = self.client.post(
                reverse('edit_payment', args=[self.expense.pk]),
                self.payment_data(),
            )

        self.assertRedirects(
            response,
            reverse('edit_payment', args=[self.expense.pk]),
        )
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.title, 'Conta atualizada')
        self.assertEqual(self.expense.description, 'Descrição atualizada')
        self.assertEqual(self.expense.payment_method, PaymentMethod.CREDIT_CARD)
        self.assertEqual(self.expense.user, self.creator)
        self.assertEqual(self.expense.creator, self.creator)
        self.assertEqual(self.expense.amount, Decimal('75.50'))
        self.assertEqual(self.expense.occurred_on, date(2026, 11, 6))
        self.assertEqual(self.expense.updated_at, updated_at)
        self.assertSetEqual(
            set(self.expense.participants.values_list('pk', flat=True)),
            {self.other_user.pk},
        )

    def test_invalid_edit_does_not_change_payment_or_update_timestamp(self):
        self.client.force_login(self.creator)
        original_updated_at = self.expense.updated_at

        response = self.client.post(
            reverse('edit_payment', args=[self.expense.pk]),
            self.payment_data(amount='-1.00'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('amount', response.context['form'].errors)
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.title, 'Conta original')
        self.assertEqual(self.expense.amount, Decimal('25.00'))
        self.assertEqual(self.expense.updated_at, original_updated_at)

    def test_updated_at_is_not_editable_on_the_model(self):
        self.assertFalse(Expense._meta.get_field('updated_at').editable)

    def test_updated_at_changes_when_saving_only_selected_fields(self):
        updated_at = timezone.now() + timedelta(minutes=1)
        self.expense.title = 'Alteração parcial'

        with patch('django.utils.timezone.now', return_value=updated_at):
            self.expense.save(update_fields=['title'])

        self.expense.refresh_from_db()
        self.assertEqual(self.expense.updated_at, updated_at)

    def test_inactive_payment_cannot_be_edited(self):
        self.expense.delete()
        self.client.force_login(self.creator)

        response = self.client.get(
            reverse('edit_payment', args=[self.expense.pk])
        )

        self.assertEqual(response.status_code, 404)

