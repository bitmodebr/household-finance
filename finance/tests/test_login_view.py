from django.test import Client, TestCase
from django.urls import reverse

from finance.models import User


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='SecurePassword123!',
            first_name='Maria',
        )

    def test_login_page_renders_email_password_and_csrf_fields(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modo Finanças')
        self.assertContains(response, 'O seu melhor investimento')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_user_can_log_in_with_email_and_password(self):
        response = self.client.post(
            reverse('login'),
            {'email': 'MARIA@example.com', 'password': 'SecurePassword123!'},
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_invalid_credentials_do_not_log_in(self):
        response = self.client.post(
            reverse('login'),
            {'email': 'maria@example.com', 'password': 'WrongPassword123!'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'E-mail ou senha inválidos.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse('login'),
            {'email': 'maria@example.com', 'password': 'SecurePassword123!'},
        )

        self.assertEqual(response.status_code, 403)
