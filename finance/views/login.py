from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render

from finance.forms import EmailLoginForm


def login(request):
    #if request.user.is_authenticated:
    #    return redirect('home')

    form = EmailLoginForm(
        request=request,
        data=request.POST if request.method == 'POST' else None,
    )

    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        return redirect('home')

    return render(request, 'login.html', {'form': form, 'title': 'Login'})
