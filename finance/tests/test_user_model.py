from django.test import TestCase
from finance.models import User


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='maria',
            password='SecurePassword123!',
            first_name='Maria',
            last_name='Silva',
            email='maria@example.com',
            cpf='529.982.247-25',
        )

    def test_user_has_first_name(self):
        self.assertEqual(self.user.first_name, 'Maria')

    def test_user_has_last_name(self):
        self.assertEqual(self.user.last_name, 'Silva')

    def test_user_has_email(self):
        self.assertEqual(self.user.email, 'maria@example.com')

    def test_user_has_cpf(self):
        self.assertEqual(self.user.cpf, '529.982.247-25')

    def test_user_password_is_stored_hashed(self):
        self.assertNotEqual(self.user.password, 'SecurePassword123!')
        self.assertTrue(self.user.check_password('SecurePassword123!'))

    def test_user_has_username(self):
        self.assertEqual(self.user.username, 'maria')

    def test_user_is_active_by_default(self):
        self.assertTrue(self.user.is_active)

    def test_regular_user_is_not_staff(self):
        self.assertFalse(self.user.is_staff)

    def test_regular_user_is_not_superuser(self):
        self.assertFalse(self.user.is_superuser)

    def test_user_has_last_login_field(self):
        self.assertIsNone(self.user.last_login)

    def test_user_has_date_joined_field(self):
        self.assertIsNotNone(self.user.date_joined)

    def test_user_has_groups_relation(self):
        self.assertTrue(User._meta.get_field('groups').many_to_many)

    def test_user_has_user_permissions_relation(self):
        self.assertTrue(User._meta.get_field('user_permissions').many_to_many)

    def test_superuser_has_admin_status(self):
        superuser = User.objects.create_superuser(
            username='admin',
            password='SecurePassword123!',
            email='admin@example.com',
        )

        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
