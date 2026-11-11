from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from finance.models import User


class UserValidationTests(TestCase):
    def create_user(self, **overrides):
        fields = {
            'first_name': 'Ana',
            'password': 'StrongPass123!',
            'email': 'ana@example.com',
            'cpf': '529.982.247-25',
        }
        fields.update(overrides)
        return User.objects.create_user(**fields)

    def test_valid_formatted_cpf_is_accepted(self):
        user = self.create_user()

        self.assertEqual(user.cpf, '529.982.247-25')

    def test_valid_unformatted_cpf_is_accepted(self):
        user = self.create_user(cpf='52998224725')

        self.assertEqual(user.cpf, '52998224725')

    def test_blank_cpf_is_accepted(self):
        user = self.create_user(cpf='')

        self.assertEqual(user.cpf, '')

    def test_invalid_cpf_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.create_user(cpf='123.456.789-00')

    def test_repeated_digits_are_not_a_valid_cpf(self):
        with self.assertRaises(ValidationError):
            self.create_user(cpf='111.111.111-11')

    def test_duplicate_cpf_is_rejected(self):
        self.create_user()

        with self.assertRaises(ValidationError):
            self.create_user(email='another@example.com')

    def test_blank_cpf_can_be_reused(self):
        self.create_user(cpf='')
        user = self.create_user(cpf='', email='another@example.com')

        self.assertEqual(user.cpf, '')

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.create_user()

        with self.assertRaises(ValidationError):
            self.create_user(email='ANA@example.com', cpf='123.456.789-09')

    def test_blank_email_can_be_reused(self):
        self.create_user(email='', cpf='')
        user = self.create_user(email='', cpf='', first_name='Bia')

        self.assertEqual(user.email, '')

    def test_duplicate_username_is_rejected(self):
        self.create_user(username='ana1234')

        with self.assertRaises(ValidationError):
            self.create_user(username='ana1234', email='another@example.com')

    def test_username_is_generated_from_first_name_and_unique_suffix(self):
        user = self.create_user()
        suffix = user.username[len('Ana'):]

        self.assertTrue(user.username.startswith('Ana'))
        self.assertEqual(len(suffix), 4)
        self.assertEqual(len(set(suffix)), 4)
        self.assertTrue(suffix.isalnum())

    def test_generated_username_retries_when_already_taken(self):
        self.create_user(username='AnaAb12')

        with patch(
            'finance.models.user_manager.get_random_string',
            side_effect=['Ab12', 'Bc23'],
        ):
            user = self.create_user(email='another@example.com', cpf='123.456.789-09')

        self.assertEqual(user.username, 'AnaBc23')

    def test_username_generation_requires_a_first_name(self):
        with self.assertRaises(ValueError):
            self.create_user(first_name='')

    def test_password_shorter_than_eight_characters_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.create_user(password='Ab1!')

    def test_password_without_a_letter_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.create_user(password='1234567!')

    def test_password_without_a_number_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.create_user(password='StrongPass!')

    def test_password_without_a_special_character_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.create_user(password='StrongPass123')

    def test_strong_password_is_accepted(self):
        user = self.create_user()

        self.assertTrue(user.check_password('StrongPass123!'))

    def test_eight_character_strong_password_is_accepted(self):
        user = self.create_user(password='Abc1!xyz')

        self.assertTrue(user.check_password('Abc1!xyz'))
