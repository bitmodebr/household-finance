from django.core.exceptions import ValidationError
from django.db import models


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
