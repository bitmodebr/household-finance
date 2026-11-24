from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from finance.forms import ExpenseForm
from finance.models import Expense


@login_required(login_url='login')
def add_payment(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        expense = form.save(commit=False)
        expense.creator = request.user
        expense.save()
        form.save_m2m()
        messages.success(request, 'Pagamento cadastrado com sucesso.')
        return redirect('add_payment')

    return render(
        request,
        'add_payment.html',
        {'form': form, 'title': 'Adicionar pagamento'},
    )


@login_required(login_url='login')
def edit_payment(request, expense_id):
    expense = get_object_or_404(
        Expense,
        pk=expense_id,
        creator=request.user,
        is_active=True,
    )
    form = ExpenseForm(
        request.POST if request.method == 'POST' else None,
        instance=expense,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pagamento atualizado com sucesso.')
        return redirect('edit_payment', expense_id=expense.pk)

    return render(
        request,
        'edit_payment.html',
        {
            'form': form,
            'expense': expense,
            'title': 'Editar pagamento',
        },
    )
