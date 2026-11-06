from django.test import TestCase
from django.urls import reverse

from finance.models import User


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

    def test_authenticated_dashboard_has_logged_in_navigation_only(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Minhas finanças')
        self.assertContains(response, 'Adicionar pagamento')
        self.assertContains(response, 'Como funciona')
        self.assertContains(response, 'Sobre nós')
        self.assertContains(response, 'Logout')
        self.assertNotContains(response, '>Login<')
        self.assertNotContains(response, '>Cadastro<')

    def test_logout_button_opens_confirmation_modal_instead_of_submitting(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

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
