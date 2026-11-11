from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from finance.models import User
from finance.validators import validate_first_name, validate_person_name


class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        validators=[validate_first_name],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'given-name',
                'placeholder': 'Seu nome',
            }
        ),
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        validators=[validate_person_name],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'family-name',
                'placeholder': 'Seus sobrenomes',
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
            last_name=self.cleaned_data.get('last_name', ''),
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
            last_name=self.cleaned_data['last_name'],
        )
