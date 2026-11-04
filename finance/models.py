from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.crypto import get_random_string
from django.utils import timezone

from finance.validators import validate_cpf


def expense_created_at():
    return timezone.now()


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


class User(AbstractUser):
    cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf])

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                condition=~Q(email=''),
                name='unique_non_empty_user_email',
            ),
            models.UniqueConstraint(
                fields=['cpf'],
                condition=~Q(cpf=''),
                name='unique_non_empty_user_cpf',
            ),
        ]


class ExpenseQuerySet(models.QuerySet):
    def delete(self):
        count = self.filter(is_active=True).update(is_active=False)
        return count, {self.model._meta.label: count}

    def update(self, **kwargs):
        if 'creator' in kwargs or 'creator_id' in kwargs:
            raise ValidationError('The creator of an expense cannot be changed.')
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if 'creator' in fields or 'creator_id' in fields:
            raise ValidationError('The creator of an expense cannot be changed.')
        return super().bulk_update(objs, fields, batch_size=batch_size)


class Expense(models.Model):
    creator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_expenses',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    occurred_on = models.DateField()
    created_at = models.DateTimeField(default=expense_created_at, editable=False)
    is_active = models.BooleanField(default=True)
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_expenses',
    )
    objects = ExpenseQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name='expense_amount_non_negative',
            ),
        ]

    def __str__(self):
        return f'{self.user}: {self.amount} on {self.occurred_on}'

    def save(self, *args, **kwargs):
        if self.pk:
            original_creator_id = (
                type(self).objects.using(kwargs.get('using')).filter(pk=self.pk)
                .values_list('creator_id', flat=True)
                .first()
            )
            if (
                original_creator_id is not None
                and original_creator_id != self.creator_id
            ):
                raise ValidationError('The creator of an expense cannot be changed.')
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        count, deleted_objects = type(self).objects.using(using).filter(
            pk=self.pk,
            is_active=True,
        ).delete()
        self.is_active = False
        return count, deleted_objects
