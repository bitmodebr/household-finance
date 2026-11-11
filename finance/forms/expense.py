from django import forms
from django.utils import timezone

from finance.models import Expense, User


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('user', 'amount', 'occurred_on', 'participants')
        labels = {
            'user': 'Pagamento lançado em nome de',
            'amount': 'Valor',
            'occurred_on': 'Data do pagamento',
            'participants': 'Compartilhantes do pagamento',
        }
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
            'occurred_on': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'participants': forms.SelectMultiple(
                attrs={'class': 'form-select', 'size': '5'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_users = User.objects.filter(is_active=True).order_by(
            'first_name',
            'username',
        )
        self.fields['user'].queryset = active_users
        self.fields['participants'].queryset = active_users
        self.fields['participants'].required = False
        self.fields['participants'].help_text = (
            'Deixe vazio para compartilhar o pagamento entre todos os usuários ativos.'
        )
        self.fields['occurred_on'].widget.attrs['max'] = timezone.localdate().isoformat()
