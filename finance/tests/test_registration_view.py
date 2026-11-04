from django.test import Client, TestCase
from django.urls import reverse

from finance.models import User


class RegistrationViewTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            'first_name': 'Ana',
            'email': 'ana@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        data.update(overrides)
        return data

    def test_registration_page_is_public_and_renders_required_fields(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertContains(response, reverse('login'))

    def test_valid_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse('register'),
            self.registration_data(),
        )

        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(email='ana@example.com')
        self.assertEqual(user.first_name, 'Ana')
        self.assertTrue(user.check_password('StrongPass123!'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_registration_preserves_submitted_form_values(self):
        response = self.client.post(
            reverse('register'),
            self.registration_data(password2='DifferentPass123!'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Ana"')
        self.assertContains(response, 'value="ana@example.com"')
        self.assertContains(response, 'As senhas não coincidem.')
        self.assertFalse(User.objects.filter(email='ana@example.com').exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username='existing',
            email='ana@example.com',
            password='SecurePassword123!',
            first_name='Ana',
        )

        response = self.client.post(
            reverse('register'),
            self.registration_data(email='ANA@example.com'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Já existe uma conta cadastrada com este e-mail.')

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            reverse('register'),
            self.registration_data(
                password1='weak',
                password2='weak',
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Esta senha é muito curta.')
        self.assertFalse(User.objects.filter(email='ana@example.com').exists())

    def test_registration_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse('register'),
            self.registration_data(),
        )

        self.assertEqual(response.status_code, 403)
