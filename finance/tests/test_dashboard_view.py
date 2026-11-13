from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from finance.models import Expense, User


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='SecurePassword123!',
            first_name='Maria',
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("dashboard")}',
        )

    def test_authenticated_user_sees_welcome_with_first_name(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h3>Seja bem vindo(a), Maria</h3>', html=True)

    def test_dashboard_does_not_expose_other_users_sensitive_information(self):
        other_user = User.objects.create_user(
            username='outro',
            email='other-private@example.com',
            password='PrivatePassword987!',
            first_name='Outro',
        )
        other_user.last_login = other_user.date_joined.replace(year=2020)
        other_user.save(update_fields=['last_login'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, other_user.email)
        self.assertNotContains(response, 'PrivatePassword987!')
        self.assertNotContains(response, other_user.password)
        self.assertNotContains(
            response,
            other_user.last_login.strftime('%Y-%m-%d %H:%M:%S'),
        )
        self.assertNotContains(response, other_user.username)

    def test_dashboard_shows_empty_payments_message_when_user_has_no_payments(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Meus pagamentos')
        self.assertContains(response, 'Você ainda não possui pagamentos.')
        self.assertEqual(response.context['payment_rows'], [])

    def test_dashboard_lists_payments_for_each_user_role_with_distinct_colors(self):
        payer = User.objects.create_user(
            username='ana',
            email='ana@example.com',
            password='SecurePassword123!',
            first_name='Ana',
        )
        participant_creator = User.objects.create_user(
            username='bia',
            email='bia@example.com',
            password='SecurePassword123!',
            first_name='Bia',
        )
        unrelated = User.objects.create_user(
            username='caio',
            email='caio@example.com',
            password='SecurePassword123!',
            first_name='Caio',
        )
        created_payment = self.create_payment(
            creator=self.user,
            payer=payer,
            amount='10.00',
        )
        payer_payment = self.create_payment(
            creator=participant_creator,
            payer=self.user,
            amount='20.00',
        )
        participant_payment = self.create_payment(
            creator=participant_creator,
            payer=payer,
            amount='30.00',
            participants=[self.user],
        )
        creator_and_payer_payment = self.create_payment(
            creator=self.user,
            payer=self.user,
            amount='31.00',
        )
        payer_and_participant_payment = self.create_payment(
            creator=participant_creator,
            payer=self.user,
            amount='32.00',
            participants=[self.user],
        )
        creator_and_participant_payment = self.create_payment(
            creator=self.user,
            payer=payer,
            amount='33.00',
            participants=[self.user],
        )
        self.create_payment(
            creator=unrelated,
            payer=unrelated,
            amount='40.00',
        )
        inactive_payment = self.create_payment(
            creator=self.user,
            payer=payer,
            amount='50.00',
            is_active=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        rows = response.context['payment_rows']
        self.assertEqual(
            {row['expense'].pk for row in rows},
            {
                created_payment.pk,
                payer_payment.pk,
                participant_payment.pk,
                creator_and_payer_payment.pk,
                payer_and_participant_payment.pk,
                creator_and_participant_payment.pk,
            },
        )
        self.assertEqual(
            len([row for row in rows if row['expense'].pk == created_payment.pk]),
            1,
        )
        self.assertEqual(
            {row['expense'].pk: row['row_class'] for row in rows},
            {
                created_payment.pk: 'table-success',
                payer_payment.pk: 'payment-payer',
                participant_payment.pk: 'table-warning',
                creator_and_payer_payment.pk: 'payment-payer',
                payer_and_participant_payment.pk: 'payment-payer',
                creator_and_participant_payment.pk: 'table-warning',
            },
        )
        self.assertNotIn(inactive_payment.pk, {row['expense'].pk for row in rows})
        self.assertContains(response, 'Criado por mim')
        self.assertContains(response, 'Sou o pagante')
        self.assertContains(response, 'Sou participante')

    def test_dashboard_shows_associated_first_names_and_ellipsis_after_two_people(self):
        payer = User.objects.create_user(
            username='ana',
            email='ana@example.com',
            password='SecurePassword123!',
            first_name='Ana',
        )
        participant_one = User.objects.create_user(
            username='bia',
            email='bia@example.com',
            password='SecurePassword123!',
            first_name='Bia',
        )
        participant_two = User.objects.create_user(
            username='caio',
            email='caio@example.com',
            password='SecurePassword123!',
            first_name='Caio',
        )
        expense = self.create_payment(
            creator=self.user,
            payer=payer,
            amount='45.75',
            participants=[participant_one, participant_two],
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        row = next(
            row for row in response.context['payment_rows']
            if row['expense'].pk == expense.pk
        )
        self.assertEqual(row['people'], ['Ana', 'Bia'])
        self.assertTrue(row['has_more_people'])
        self.assertContains(response, 'Ana')
        self.assertContains(response, 'Bia')
        self.assertNotContains(response, 'Caio')
        self.assertContains(response, 'Mais pessoas associadas')
        self.assertContains(response, 'R$ 45,75')

    def test_payment_row_links_to_future_edit_path_without_adding_an_edit_route(self):
        expense = self.create_payment(
            creator=self.user,
            payer=self.user,
            amount='12.50',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(
            response,
            f'href="/pagamentos/{expense.pk}/editar/"',
        )
        self.assertEqual(
            self.client.get(f'/pagamentos/{expense.pk}/editar/').status_code,
            404,
        )

    def create_payment(
        self,
        *,
        creator,
        payer,
        amount,
        participants=(),
        is_active=True,
    ):
        expense = Expense.objects.create(
            creator=creator,
            user=payer,
            amount=Decimal(amount),
            occurred_on=date(2026, 11, 10),
            is_active=is_active,
        )
        expense.participants.set(participants)
        return expense

    def test_authenticated_dashboard_has_logged_in_navigation_only(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Minhas finanças')
        self.assertContains(response, 'Adicionar pagamento')
        self.assertContains(response, 'Como funciona')
        self.assertContains(response, 'Sobre nós')
        self.assertContains(response, 'aria-label="Meus dados"')
        self.assertNotContains(response, '>Login<')
        self.assertNotContains(response, '>Cadastro<')
        self.assertNotContains(response, 'data-bs-target="#logoutConfirmation"')

    def test_profile_logout_button_opens_confirmation_modal_instead_of_submitting(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('profile'))

        self.assertContains(response, 'data-bs-toggle="modal"')
        self.assertContains(response, 'data-bs-target="#logoutConfirmation"')
        self.assertContains(response, 'id="logoutConfirmation"')
        self.assertContains(response, 'Tem certeza de que deseja sair da sua conta?')
        self.assertContains(response, 'form="logout-form"')
        self.assertContains(response, 'class="btn btn-outline-light rounded-pill fw-semibold"')

    def test_logout_cannot_be_triggered_by_get_request(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_submits_post_and_ends_the_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)


class PublicNavigationTests(TestCase):
    def test_anonymous_user_sees_public_navigation_only(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Sobre nós')
        self.assertContains(response, 'Como funciona')
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Cadastro')
        self.assertNotContains(response, 'Minhas finanças')
        self.assertNotContains(response, 'Adicionar pagamento')
        self.assertNotContains(response, 'Logout')

    def test_authenticated_user_is_redirected_from_home_to_dashboard(self):
        user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='SecurePassword123!',
            first_name='Maria',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertRedirects(response, reverse('dashboard'))
