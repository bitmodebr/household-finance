from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from finance.forms import UserProfileForm


@login_required(login_url='login')
def profile(request):
    form = UserProfileForm(
        data=request.POST if request.method == 'POST' else None,
        instance=request.user,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Seus dados foram atualizados com sucesso.')
        return redirect('profile')

    return render(
        request,
        'profile.html',
        {'form': form, 'title': 'Meus dados', 'profile_page': True},
    )
