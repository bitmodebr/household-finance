from django.test import TestCase
from django.urls import reverse

from finance.models import User


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='maria',
            email='maria@example.com',
            password='SecurePassword123!',
            first_name='Maria',
            last_name='Silva',
            cpf='529.982.247-25',
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('profile'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("profile")}',
        )

    def test_profile_displays_authenticated_users_data_and_logout_action(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        for field in ('first_name', 'last_name', 'username', 'email', 'cpf'):
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, 'value="Maria"')
        self.assertContains(response, 'value="Silva"')
        self.assertContains(response, 'value="maria"')
        self.assertContains(response, 'value="maria@example.com"')
        self.assertContains(response, 'value="529.982.247-25"')
        self.assertContains(response, 'Salvar alterações')
        self.assertContains(response, 'data-bs-target="#logoutConfirmation"')
        self.assertContains(response, 'Sair')
        self.assertNotContains(response, 'aria-label="Meus dados"')

    def test_profile_updates_only_the_authenticated_users_personal_data(self):
        other_user = User.objects.create_user(
            username='outro',
            email='outro@example.com',
            password='SecurePassword456!',
            first_name='Outro',
            last_name='Usuario',
            cpf='111.444.777-35',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('profile'),
            {
                'first_name': 'Maria Clara',
                'last_name': 'Souza',
                'username': 'mariaclara',
                'email': 'maria.clara@example.com',
                'cpf': '935.411.347-80',
                'user_id': other_user.pk,
                'is_superuser': 'on',
            },
        )

        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        other_user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Maria Clara')
        self.assertEqual(self.user.last_name, 'Souza')
        self.assertEqual(self.user.username, 'mariaclara')
        self.assertEqual(self.user.email, 'maria.clara@example.com')
        self.assertEqual(self.user.cpf, '935.411.347-80')
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(other_user.first_name, 'Outro')
        self.assertEqual(other_user.last_name, 'Usuario')
        self.assertEqual(other_user.username, 'outro')
        self.assertEqual(other_user.email, 'outro@example.com')
        self.assertEqual(other_user.cpf, '111.444.777-35')

    def test_invalid_profile_data_is_not_saved(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('profile'),
            {
                'first_name': 'Maria',
                'last_name': 'Silva',
                'username': 'maria',
                'email': 'not-an-email',
                'cpf': '529.982.247-25',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informe um endereço de email válido.')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'maria@example.com')

    def test_authenticated_navigation_links_to_profile_icon_on_other_pages(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'aria-label="Meus dados"')
        self.assertContains(response, f'href="{reverse("profile")}"')
        self.assertContains(response, '<svg')
        self.assertNotContains(response, 'data-bs-target="#logoutConfirmation"')
