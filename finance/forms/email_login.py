from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError


class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'email',
                'placeholder': 'seu@email.com',
            }
        ),
    )
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'current-password',
                'placeholder': 'Digite sua senha',
            }
        ),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user_model = get_user_model()
            try:
                user = user_model._default_manager.get(email__iexact=email)
            except user_model.DoesNotExist:
                user = None

            if user is not None:
                self.user_cache = authenticate(
                    self.request,
                    username=user.get_username(),
                    password=password,
                )

            if self.user_cache is None:
                raise ValidationError('E-mail ou senha inválidos.')

        return cleaned_data

    def get_user(self):
        return self.user_cache
