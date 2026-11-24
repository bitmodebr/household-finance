from datetime import date
from decimal import Decimal

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.utils import timezone

from finance.services import Finance


class MonthFilterForm(forms.Form):
    month = forms.ChoiceField(
        label='Mês',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'invalid_choice': 'Selecione um mês válido.'},
    )

    def __init__(self, *args, current_month=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_month = current_month or timezone.localdate().replace(day=1)
        self.fields['month'].choices = [
            (month.strftime('%Y-%m'), month.strftime('%m/%Y'))
            for month in _available_months(self.current_month)
        ]
        self.fields['month'].initial = self.current_month.strftime('%Y-%m')

    def clean_month(self):
        month = _parse_month(self.cleaned_data['month'])
        if month is None:
            raise ValidationError('Selecione um mês válido.')
        return month


def _available_months(current_month):
    month_index = current_month.year * 12 + current_month.month - 1
    for offset in range(14):
        year, month_index_in_year = divmod(month_index - offset, 12)
        yield date(year, month_index_in_year + 1, 1)


def _parse_month(value):
    if not isinstance(value, str):
        return None
    try:
        year, month = value.split('-')
        if len(year) != 4 or len(month) != 2:
            return None
        return date(int(year), int(month), 1)
    except ValueError:
        return None


def _monthly_finance_data(user_id, selected_month):
    finance = Finance(selected_month.year, selected_month.month)
    daily_amounts = finance.calculate_user_daily_amounts(user_id)
    payment_rows = finance.calculate_user_payment_settlements(user_id)
    settlement_total = sum(
        (payment.amount for payment in payment_rows),
        Decimal('0.00'),
    )
    return {
        'chart_payload': {
            'labels': [str(day.day) for day in daily_amounts],
            'datasets': [
                {
                    'label': 'Pago por mim',
                    'data': [
                        float(amounts.paid) for amounts in daily_amounts.values()
                    ],
                    'backgroundColor': '#198754',
                    'borderColor': '#146c43',
                    'borderWidth': 1,
                },
                {
                    'label': 'Minha parte nos pagamentos',
                    'data': [
                        float(amounts.share) for amounts in daily_amounts.values()
                    ],
                    'backgroundColor': '#dc3545',
                    'borderColor': '#b02a37',
                    'borderWidth': 1,
                },
            ],
        },
        'payment_rows': payment_rows,
        'settlement_state': (
            'receive'
            if settlement_total < 0
            else 'pay' if settlement_total > 0 else 'balanced'
        ),
        'settlement_amount': abs(settlement_total),
    }


@login_required(login_url='login')
def my_finances(request):
    current_month = timezone.localdate().replace(day=1)
    has_month_filter = 'month' in request.GET
    current_month_value = current_month.strftime('%Y-%m')
    requested_month = _parse_month(request.GET.get('month'))
    is_future_month = requested_month is not None and requested_month > current_month
    form = MonthFilterForm(
        data=(
            {'month': current_month_value}
            if is_future_month
            else request.GET if has_month_filter else None
        ),
        current_month=current_month,
    )

    selected_month = current_month
    finance_data = None
    filter_message = None
    if is_future_month:
        filter_message = (
            'Não é possível selecionar um mês futuro. '
            'Exibindo os dados do mês atual.'
        )
        finance_data = _monthly_finance_data(request.user.pk, selected_month)
    elif not has_month_filter or form.is_valid():
        if has_month_filter:
            selected_month = form.cleaned_data['month']
        finance_data = _monthly_finance_data(request.user.pk, selected_month)

    return render(
        request,
        'my_finances.html',
        {
            'title': 'Minhas Finanças',
            'form': form,
            'selected_month': selected_month,
            'filter_message': filter_message,
            **(
                finance_data
                if finance_data is not None
                else {
                    'chart_payload': None,
                    'payment_rows': [],
                    'settlement_state': 'balanced',
                    'settlement_amount': Decimal('0.00'),
                }
            ),
        },
    )
