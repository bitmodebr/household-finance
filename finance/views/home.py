from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import redirect, render

from finance.models import Expense, User


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html', {'title': 'Início'})


@login_required(login_url='login')
def dashboard(request):
    payments = (
        Expense.objects.filter(is_active=True)
        .filter(
            Q(creator=request.user)
            | Q(user=request.user)
            | Q(participants=request.user)
        )
        .select_related('creator', 'user')
        .prefetch_related(
            Prefetch(
                'participants',
                queryset=User.objects.order_by('first_name', 'username'),
            )
        )
        .distinct()
        .order_by('-created_at', '-pk')
    )

    payment_rows = []
    for payment in payments:
        participants = list(payment.participants.all())
        associated_users = [payment.user]
        associated_users.extend(
            participant
            for participant in participants
            if participant.pk != payment.user_id
        )
        associated_names = [
            person.first_name or person.get_username()
            for person in associated_users
        ]

        is_participant = any(
            participant.pk == request.user.pk
            for participant in participants
        )
        if payment.user_id == request.user.pk:
            row_class = 'payment-payer'
        elif is_participant:
            row_class = 'table-warning'
        elif payment.creator_id == request.user.pk:
            row_class = 'table-success'
        else:
            raise RuntimeError('Dashboard payment has no matching user role.')

        payment_rows.append(
            {
                'expense': payment,
                'creator_name': payment.creator.get_username()
                or payment.creator.get_full_name(),
                'people': associated_names[:2],
                'has_more_people': len(associated_names) > 2,
                'row_class': row_class,
            }
        )

    return render(
        request,
        'dashboard.html',
        {'title': 'Dashboard', 'payment_rows': payment_rows},
    )
