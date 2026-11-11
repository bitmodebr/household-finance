from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from finance.models.expense_queryset import ExpenseQuerySet
from finance.validators import validate_expense_date_not_future


def expense_created_at():
    return timezone.now()


class Expense(models.Model):
    creator = models.ForeignKey(
        'finance.User',
        on_delete=models.PROTECT,
        related_name='created_expenses',
    )
    user = models.ForeignKey(
        'finance.User',
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    occurred_on = models.DateField(
        validators=[validate_expense_date_not_future],
        verbose_name='data do pagamento',
    )
    created_at = models.DateTimeField(default=expense_created_at, editable=False)
    is_active = models.BooleanField(default=True)
    participants = models.ManyToManyField(
        'finance.User',
        blank=True,
        related_name='shared_expenses',
        verbose_name='compartilhantes do pagamento',
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
