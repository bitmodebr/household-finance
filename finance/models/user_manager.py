from django.contrib.auth.models import UserManager as DjangoUserManager
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string


class UserManager(DjangoUserManager):
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            username = self.generate_username(extra_fields.get('first_name', ''))

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **extra_fields,
        )
        validate_password(password, user)
        user.full_clean(exclude=['password'])
        user.set_password(password)
        user.save(using=self._db)
        return user

    def generate_username(self, first_name):
        base = self.model.normalize_username(first_name)
        base = ''.join(character for character in base if character.isalnum())[:146]
        if not base:
            raise ValueError('A first name is required to generate a username.')

        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for _ in range(100):
            suffix = get_random_string(4, allowed_chars=alphabet)
            if len(set(suffix)) != 4:
                continue
            username = f'{base}{suffix}'
            if not self.get_queryset().filter(username__iexact=username).exists():
                return username

        raise RuntimeError('Could not generate a unique username after 100 attempts.')
