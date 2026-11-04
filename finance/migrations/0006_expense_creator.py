import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import F


def assign_existing_creators(apps, schema_editor):
    Expense = apps.get_model('finance', 'Expense')
    Expense.objects.using(schema_editor.connection.alias).filter(
        creator__isnull=True,
    ).update(creator_id=F('user_id'))


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_expense_created_at_expense_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='creator',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='created_expenses',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            assign_existing_creators,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='expense',
            name='creator',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='created_expenses',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
