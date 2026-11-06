from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from finance.forms import ExpenseForm
from finance.models import Expense, User


class AddPaymentViewTests(TestCase):
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

    def payment_data(self, **overrides):
        data = {
            'user': str(self.other_user.pk),
            'amount': '45.75',
            'occurred_on': '2026-11-05',
            'participants': [str(self.creator.pk), str(self.other_user.pk)],
        }
        data.update(overrides)
        return data

    def test_anonymous_user_is_redirected_from_add_payment_page(self):
        response = self.client.get(reverse('add_payment'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("add_payment")}',
        )

    def test_anonymous_user_cannot_create_payment(self):
        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(),
        )

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("add_payment")}',
        )
        self.assertFalse(Expense.objects.exists())

    def test_authenticated_user_sees_payment_form_and_branding(self):
        self.client.force_login(self.creator)

        with patch(
            'django.utils.timezone.localdate',
            return_value=date(2026, 11, 6),
        ):
            response = self.client.get(reverse('add_payment'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FinanceMode')
        self.assertContains(response, 'O seu melhor investimento')
        self.assertContains(response, 'Cadastrar pagamento')
        self.assertContains(response, reverse('add_payment'))
        self.assertContains(response, 'Adicionar pagamento')
        self.assertContains(response, 'max="2026-11-06"')
        self.assertContains(response, 'Compartilhantes do pagamento')

    def test_authenticated_user_can_create_payment_on_behalf_of_another_user(self):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(),
        )

        expense = Expense.objects.get()
        self.assertRedirects(response, reverse('add_payment'))
        self.assertEqual(expense.creator, self.creator)
        self.assertEqual(expense.user, self.other_user)
        self.assertEqual(expense.amount, Decimal('45.75'))
        self.assertEqual(expense.occurred_on, date(2026, 11, 5))
        self.assertSetEqual(
            set(expense.participants.values_list('pk', flat=True)),
            {self.creator.pk, self.other_user.pk},
        )

    def test_submitted_creator_cannot_override_authenticated_user(self):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(creator=str(self.other_user.pk)),
        )

        expense = Expense.objects.get()
        self.assertRedirects(response, reverse('add_payment'))
        self.assertEqual(expense.creator, self.creator)

    def test_invalid_payment_is_not_created_and_form_errors_are_rendered(self):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(amount='-1.00'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('amount', response.context['form'].errors)
        self.assertFalse(Expense.objects.exists())

    def test_inactive_users_cannot_be_selected_as_payer_or_participants(self):
        inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='SecurePassword123!',
            is_active=False,
        )
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(
                user=str(inactive_user.pk),
                participants=[str(inactive_user.pk)],
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.context['form'].errors)
        self.assertIn('participants', response.context['form'].errors)
        self.assertFalse(Expense.objects.exists())

    @patch('finance.validators.timezone.localdate', return_value=date(2026, 11, 6))
    def test_payment_date_cannot_be_after_sao_paulo_current_date(self, mocked_today):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(occurred_on='2026-11-07'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('occurred_on', response.context['form'].errors)
        self.assertFalse(Expense.objects.exists())
        mocked_today.assert_called()

    @patch('finance.validators.timezone.localdate', return_value=date(2026, 11, 6))
    def test_payment_on_current_sao_paulo_date_is_accepted(self, mocked_today):
        self.client.force_login(self.creator)

        response = self.client.post(
            reverse('add_payment'),
            self.payment_data(occurred_on='2026-11-06'),
        )

        self.assertRedirects(response, reverse('add_payment'))
        self.assertEqual(Expense.objects.get().occurred_on, date(2026, 11, 6))
        mocked_today.assert_called()

    @patch('finance.validators.timezone.localdate', return_value=date(2026, 11, 6))
    def test_admin_model_form_rejects_future_payment_date(self, mocked_today):
        form = ExpenseForm(
            data={
                'user': self.other_user.pk,
                'amount': '45.75',
                'occurred_on': '2026-11-07',
                'participants': [],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('occurred_on', form.errors)
        mocked_today.assert_called()

    def test_participant_model_field_uses_shared_payer_label(self):
        self.assertEqual(
            Expense._meta.get_field('participants').verbose_name,
            'compartilhantes do pagamento',
        )
