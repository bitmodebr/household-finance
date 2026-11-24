from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from finance.models import Expense, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Dados financeiros', {'fields': ('cpf',)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Dados financeiros', {'fields': ('cpf',)}),
    )
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'cpf')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'creator',
        'user',
        'amount',
        'occurred_on',
        'created_at',
        'is_active',
    )
    list_filter = ('is_active', 'occurred_on')
    search_fields = (
        'creator__username',
        'user__username',
        'user__email',
    )
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at', 'creator')
    date_hierarchy = 'occurred_on'

    def get_queryset(self, request):
        return super().get_queryset(request).filter(creator=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.creator_id != request.user.pk:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.creator_id != request.user.pk:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        super().save_model(request, obj, form, change)
