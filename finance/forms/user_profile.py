from django import forms

from finance.models import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'cpf')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Nome de usuário',
            'email': 'E-mail',
            'cpf': 'CPF',
        }
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'given-name'}
            ),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'family-name'}
            ),
            'username': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'username'}
            ),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'autocomplete': 'email'}
            ),
            'cpf': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'}
            ),
        }
