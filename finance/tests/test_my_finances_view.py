from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from finance.models import Expense, User


class MyFinancesViewTests(TestCase):
    def setUp(self):
        self.user = self.create_user('ana')
        self.other_user = self.create_user('bia')
        self.third_user = self.create_user('caio')

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            first_name=username.title(),
            password='SecurePassword123!',
        )

    def create_expense(
        self,
        *,
        payer,
        amount,
        occurred_on,
        creator=None,
        participants=(),
        is_active=True,
    ):
        expense = Expense.objects.create(
            title='Pagamento',
            payment_method='pix',
            creator=creator or payer,
            user=payer,
            amount=Decimal(amount),
            occurred_on=occurred_on,
            is_active=is_active,
        )
        expense.participants.set(participants)
        return expense

    def test_anonymous_user_is_redirected_from_my_finances(self):
        response = self.client.get(reverse('my_finances'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("my_finances")}',
        )

    @patch(
        'finance.views.finances.timezone.localdate',
        return_value=date(2026, 8, 15),
    )
    def test_chart_defaults_to_the_current_month(self, mocked_today):
        self.client.force_login(self.user)

        response = self.client.get(reverse('my_finances'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Minhas Finanças')
        self.assertContains(response, 'value="2026-08"')
        self.assertContains(response, '<select')
        self.assertNotContains(response, 'type="month"')
        self.assertContains(response, 'dailyFinanceChart')
        self.assertEqual(response.context['selected_month'], date(2026, 8, 1))
        self.assertEqual(len(response.context['chart_payload']['labels']), 31)
        month_options = [
            value
            for value, _ in response.context['form'].fields['month'].choices
        ]
        self.assertEqual(len(month_options), 14)
        self.assertEqual(month_options[0], '2026-08')
        self.assertEqual(month_options[-1], '2025-07')
        mocked_today.assert_called_once()

    @patch(
        'finance.views.finances.timezone.localdate',
        return_value=date(2026, 8, 15),
    )
    def test_submitted_future_month_displays_the_current_month(self, mocked_today):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-09'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_month'], date(2026, 8, 1))
        self.assertEqual(
            response.context['form']['month'].value(),
            '2026-08',
        )
        self.assertContains(response, 'Exibindo os dados do mês atual.')
        mocked_today.assert_called_once()

    def test_month_filter_shows_daily_payment_and_share_values(self):
        self.create_expense(
            payer=self.user,
            amount='200.00',
            occurred_on=date(2026, 8, 3),
            participants=[self.other_user, self.third_user],
        )
        self.create_expense(
            payer=self.other_user,
            amount='300.00',
            occurred_on=date(2026, 8, 5),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.create_expense(
            payer=self.user,
            amount='900.00',
            occurred_on=date(2026, 7, 3),
        )
        self.create_expense(
            payer=self.user,
            amount='500.00',
            occurred_on=date(2026, 8, 7),
            is_active=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-08'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_month'], date(2026, 8, 1))
        datasets = response.context['chart_payload']['datasets']
        paid_amounts = datasets[0]['data']
        shared_amounts = datasets[1]['data']
        self.assertEqual(datasets[0]['label'], 'Pago por mim')
        self.assertEqual(datasets[1]['label'], 'Minha parte nos pagamentos')
        self.assertEqual(paid_amounts[2], 200.0)
        self.assertEqual(shared_amounts[2], 0.0)
        self.assertEqual(paid_amounts[4], 0.0)
        self.assertEqual(shared_amounts[4], 100.0)
        self.assertEqual(paid_amounts[6], 0.0)
        self.assertNotContains(response, '900.00')
        self.assertNotContains(response, '500.00')

    def test_payment_table_and_summary_show_net_monthly_settlements(self):
        paid_payment = self.create_expense(
            payer=self.user,
            amount='300.00',
            occurred_on=date(2026, 8, 3),
            participants=[self.user, self.other_user, self.third_user],
        )
        shared_payment = self.create_expense(
            payer=self.other_user,
            amount='300.00',
            occurred_on=date(2026, 8, 5),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.create_expense(
            creator=self.user,
            payer=self.other_user,
            amount='90.00',
            occurred_on=date(2026, 8, 7),
            participants=[self.other_user, self.third_user],
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-08'},
        )

        rows = response.context['payment_rows']
        self.assertEqual(
            [(row.expense.pk, row.amount) for row in rows],
            [
                (paid_payment.pk, Decimal('-200.00')),
                (shared_payment.pk, Decimal('100.00')),
            ],
        )
        self.assertEqual(
            response.context['settlement_state'],
            'receive',
        )
        self.assertEqual(
            response.context['settlement_amount'],
            Decimal('100.00'),
        )
        self.assertContains(response, 'Pagamento total')
        self.assertContains(response, 'Criador')
        self.assertContains(response, 'Data da compra')
        self.assertContains(response, 'Valor a ser pago')
        self.assertContains(
            response,
            '<span class="text-success">R$ 100,00</span>',
            html=True,
        )

    def test_positive_monthly_settlement_uses_payment_wording_and_red_value(self):
        self.create_expense(
            payer=self.other_user,
            amount='300.00',
            occurred_on=date(2026, 8, 5),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-08'},
        )

        self.assertEqual(
            response.context['settlement_state'],
            'pay',
        )
        self.assertEqual(
            response.context['settlement_amount'],
            Decimal('100.00'),
        )
        self.assertContains(
            response,
            '<span class="text-danger">R$ 100,00</span>',
            html=True,
        )
        self.assertContains(response, 'Você deve pagar esse mês:')

    def test_payment_details_net_all_expenses_per_connected_user(self):
        davi = self.create_user('davi')
        self.create_expense(
            payer=self.user,
            amount='300.00',
            occurred_on=date(2026, 8, 3),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.create_expense(
            payer=self.other_user,
            amount='600.00',
            occurred_on=date(2026, 8, 5),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.create_expense(
            payer=self.other_user,
            amount='300.00',
            occurred_on=date(2026, 8, 6),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.create_expense(
            creator=self.user,
            payer=davi,
            amount='90.00',
            occurred_on=date(2026, 8, 7),
            participants=[davi, self.third_user],
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-08'},
        )

        rows = response.context['counterparty_rows']
        self.assertEqual(
            [(row['name'], row['balance']) for row in rows],
            [
                ('Bia', Decimal('-200.00')),
                ('Caio', Decimal('100.00')),
            ],
        )
        self.assertContains(response, 'Detalhes dos pagamentos')
        self.assertContains(
            response,
            'Você deve pagar <span class="text-danger">R$ 200,00</span> à Bia',
            html=True,
        )
        self.assertContains(
            response,
            'Você deve receber <span class="text-success">R$ 100,00</span> de Caio',
            html=True,
        )
        self.assertNotContains(response, 'Davi')
        self.assertContains(response, 'counterparty-balances-table')

    def test_connected_user_with_zero_net_balance_is_still_listed(self):
        self.create_expense(
            payer=self.user,
            amount='300.00',
            occurred_on=date(2026, 8, 3),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.create_expense(
            payer=self.other_user,
            amount='300.00',
            occurred_on=date(2026, 8, 5),
            participants=[self.user, self.other_user, self.third_user],
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-08'},
        )

        rows = response.context['counterparty_rows']
        self.assertEqual(len(rows), 2)
        bia_row = next(row for row in rows if row['name'] == 'Bia')
        self.assertEqual(bia_row['balance'], Decimal('0.00'))
        self.assertRegex(
            response.content.decode(),
            r'Você não tem valores pendentes com\s+Bia',
        )

    def test_invalid_month_filter_shows_validation_error_without_a_chart(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('my_finances'),
            {'month': '2026-13'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecione um mês válido.')
        self.assertIsNone(response.context['chart_payload'])

