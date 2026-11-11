from django.test import Client, TestCase
from django.urls import reverse

from finance.forms import UserRegistrationForm
from finance.models import User


class RegistrationViewTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            'first_name': 'Ana',
            'last_name': 'Silva',
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
        self.assertContains(response, 'name="last_name"')
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
        self.assertEqual(user.last_name, 'Silva')
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

    def test_registration_does_not_create_users_with_invalid_names(self):
        invalid_names = (
            {'first_name': 'Ana Maria Clara'},
            {'first_name': 'Ana2'},
            {'last_name': 'Silva@'},
        )

        for index, overrides in enumerate(invalid_names):
            with self.subTest(overrides=overrides):
                email = f'ana{index}@example.com'
                response = self.client.post(
                    reverse('register'),
                    self.registration_data(email=email, **overrides),
                )

                self.assertEqual(response.status_code, 200)
                self.assertFalse(User.objects.filter(email=email).exists())

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

    def test_registration_requires_first_and_last_names(self):
        for field in ('first_name', 'last_name'):
            with self.subTest(field=field):
                data = self.registration_data()
                data[field] = ''

                form = UserRegistrationForm(data)

                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_first_name_accepts_one_or_two_words_with_name_punctuation(self):
        for name in ('Ana', 'Ana Maria', "Ana D'Ávila", 'Ana-Maria'):
            with self.subTest(name=name):
                form = UserRegistrationForm(
                    self.registration_data(first_name=name)
                )

                self.assertTrue(form.is_valid(), form.errors)

    def test_first_name_rejects_more_than_two_words(self):
        form = UserRegistrationForm(
            self.registration_data(first_name='Ana Maria Clara')
        )

        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_first_name_rejects_digits_and_non_name_characters(self):
        for name in ('Ana2', 'Ana@', 'Ana%', 'Ana!', 'Ana_', '2Ana'):
            with self.subTest(name=name):
                form = UserRegistrationForm(
                    self.registration_data(first_name=name)
                )

                self.assertFalse(form.is_valid())
                self.assertIn('first_name', form.errors)

    def test_last_name_accepts_multiple_words_up_to_model_limit(self):
        surname = ('A ' * 74) + 'AA'
        self.assertEqual(len(surname), 150)
        form = UserRegistrationForm(self.registration_data(last_name=surname))

        self.assertTrue(form.is_valid(), form.errors)

    def test_last_name_rejects_digits_and_non_name_characters(self):
        for surname in ('Silva2', 'Silva@', 'Silva%', 'Silva!', 'Silva_'):
            with self.subTest(surname=surname):
                form = UserRegistrationForm(
                    self.registration_data(last_name=surname)
                )

                self.assertFalse(form.is_valid())
                self.assertIn('last_name', form.errors)

    def test_last_name_rejects_values_longer_than_model_limit(self):
        form = UserRegistrationForm(
            self.registration_data(last_name='S' * 151)
        )

        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)
