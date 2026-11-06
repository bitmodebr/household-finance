from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html', {'title': 'Início'})


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard.html', {'title': 'Dashboard'})
