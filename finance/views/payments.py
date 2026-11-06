from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from finance.forms import ExpenseForm


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
