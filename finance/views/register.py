from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import redirect, render

from finance.forms import UserRegistrationForm


def register(request):
    form = UserRegistrationForm(
        data=request.POST if request.method == 'POST' else None,
    )

    if request.method == 'POST' and form.is_valid():
        try:
            form.save()
        except ValidationError as error:
            form.add_error(None, error)
        except IntegrityError:
            form.add_error(
                'email',
                'Já existe uma conta cadastrada com este e-mail.',
            )
        else:
            return redirect('login')

    return render(request, 'register.html', {'form': form, 'title': 'Cadastro'})
