from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from finance.models.user_manager import UserManager
from finance.validators import validate_cpf


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
