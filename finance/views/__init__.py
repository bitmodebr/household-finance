from finance.views.home import dashboard
from finance.views.home import home
from finance.views.finances import my_finances
from finance.views.login import login
from finance.views.payments import add_payment, edit_payment
from finance.views.profile import profile
from finance.views.register import register

__all__ = [
    'add_payment',
    'dashboard',
    'edit_payment',
    'home',
    'login',
    'my_finances',
    'profile',
    'register',
]