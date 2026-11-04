from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from finance.models import User


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


class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'given-name',
                'placeholder': 'Seu nome',
            }
        ),
    )
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
    password1 = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'new-password',
            }
        ),
    )
    password2 = forms.CharField(
        label='Confirme a senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'new-password',
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Já existe uma conta cadastrada com este e-mail.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data['password2']
        if password1 and password1 != password2:
            raise ValidationError('As senhas não coincidem.')

        user = User(
            first_name=self.cleaned_data.get('first_name', ''),
            email=self.cleaned_data.get('email', ''),
        )
        validate_password(password2, user)
        return password2

    def save(self):
        if not self.is_valid():
            raise ValueError('Cannot save an invalid registration form.')

        return User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
        )
