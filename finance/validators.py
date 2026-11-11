import re
import unicodedata

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validate_person_name(value):
    if not value:
        return

    for index, character in enumerate(value):
        category = unicodedata.category(character)
        if category.startswith('L'):
            continue
        if category.startswith('M'):
            if index == 0 or not (
                unicodedata.category(value[index - 1]).startswith(('L', 'M'))
            ):
                raise ValidationError(
                    _('Use apenas letras e separadores comuns em nomes de pessoas.'),
                    code='invalid_person_name',
                )
            continue
        if character in " '-’":
            previous_is_letter = (
                index > 0
                and unicodedata.category(value[index - 1]).startswith(('L', 'M'))
            )
            next_is_letter = (
                index + 1 < len(value)
                and unicodedata.category(value[index + 1]).startswith('L')
            )
            if previous_is_letter and next_is_letter:
                continue
        raise ValidationError(
            _('Use apenas letras e separadores comuns em nomes de pessoas.'),
            code='invalid_person_name',
        )


def validate_first_name(value):
    validate_person_name(value)
    if len(value.split()) > 2:
        raise ValidationError(
            _('Informe no máximo duas palavras no nome.'),
            code='too_many_first_name_words',
        )


def validate_cpf(value):
    if value == '':
        return

    if not re.fullmatch(r'(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})', value):
        raise ValidationError(_('Enter a valid CPF.'), code='invalid_cpf')

    digits = re.sub(r'\D', '', value)
    if len(set(digits)) == 1:
        raise ValidationError(_('Enter a valid CPF.'), code='invalid_cpf')

    first_digit = sum(
        int(digit) * weight for digit, weight in zip(digits[:9], range(10, 1, -1))
    )
    first_digit = (first_digit * 10) % 11
    if first_digit == 10:
        first_digit = 0

    second_digit = sum(
        int(digit) * weight for digit, weight in zip(digits[:10], range(11, 1, -1))
    )
    second_digit = (second_digit * 10) % 11
    if second_digit == 10:
        second_digit = 0

    if digits[-2:] != f'{first_digit}{second_digit}':
        raise ValidationError(_('Enter a valid CPF.'), code='invalid_cpf')


def validate_expense_date_not_future(value):
    if value > timezone.localdate():
        raise ValidationError(
            _('A data do pagamento não pode ser posterior à data atual.'),
            code='future_expense_date',
        )


class PasswordStrengthValidator:
    def validate(self, password, user=None):
        if password is None or len(password) < 8:
            raise ValidationError(
                _('Password must contain at least 8 characters.'),
                code='password_too_short',
            )
        if not any(character.isalpha() for character in password):
            raise ValidationError(
                _('Password must contain at least one letter.'),
                code='password_no_letter',
            )
        if not any(character.isdigit() for character in password):
            raise ValidationError(
                _('Password must contain at least one number.'),
                code='password_no_number',
            )
        if not any(not character.isalnum() for character in password):
            raise ValidationError(
                _('Password must contain at least one special character.'),
                code='password_no_special_character',
            )

    def get_help_text(self):
        return _(
            'Your password must be at least 8 characters long and include a '
            'letter, a number, and a special character.'
        )
