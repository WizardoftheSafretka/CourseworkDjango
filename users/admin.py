from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'is_active', 'is_blocked', 'is_staff',
                    'role', 'date_joined')
    list_filter = ('is_active', 'is_blocked', 'is_staff', 'is_superuser', 'groups', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('last_login', 'date_joined', 'token')

    # Переопределяем ordering, убираем username
    ordering = ('-date_joined',)  # Сортировка по дате регистрации (новые сверху)

    def get_queryset(self, request):
        """Ограничиваем доступ к данным в зависимости от роли"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_perm('users.can_view_all_users'):
            return qs
        # Обычные пользователи видят только себя
        return qs.filter(id=request.user.id)

    def get_fieldsets(self, request, obj=None):
        """Настраиваем отображаемые поля в зависимости от роли"""
        if request.user.is_superuser or request.user.has_perm('users.can_block_users'):
            return (
                (None, {'fields': ('email', 'password')}),
                (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number')}),
                (_('Permissions'),
                 {'fields': ('is_active', 'is_blocked', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
                (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
                (_('Token'), {'fields': ('token',)}),
            )
        else:
            # Обычные пользователи не видят поля прав
            return (
                (None, {'fields': ('email',)}),
                (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number')}),
                (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            )

    def get_list_display(self, request):
        """Настраиваем отображаемые колонки в зависимости от роли"""
        if request.user.is_superuser or request.user.has_perm('users.can_view_all_users'):
            return ('id', 'email', 'first_name', 'last_name', 'phone_number', 'is_active', 'is_blocked', 'is_staff',
                    'role', 'date_joined')
        return ('id', 'email', 'first_name', 'last_name', 'phone_number', 'date_joined')

    def get_actions(self, request):
        """Настраиваем доступные действия в зависимости от роли"""
        actions = super().get_actions(request)
        if not (request.user.is_superuser or request.user.has_perm('users.can_block_users')):
            actions.pop('block_users', None)
            actions.pop('unblock_users', None)
        return actions

    def role(self, obj):
        """Отображение роли пользователя"""
        if obj.is_superuser:
            return 'Суперпользователь'
        if obj.is_manager:
            return 'Менеджер'
        return 'Пользователь'

    role.short_description = 'Роль'

    actions = ['block_users', 'unblock_users', 'activate_users', 'deactivate_users']

    def block_users(self, request, queryset):
        """Заблокировать выбранных пользователей"""
        if not (request.user.is_superuser or request.user.has_perm('users.can_block_users')):
            self.message_user(request, 'У вас нет прав на блокировку пользователей', level='ERROR')
            return
        updated = queryset.update(is_blocked=True)
        self.message_user(request, f'Заблокировано {updated} пользователей(я)')

    block_users.short_description = 'Заблокировать выбранных пользователей'

    def unblock_users(self, request, queryset):
        """Разблокировать выбранных пользователей"""
        if not (request.user.is_superuser or request.user.has_perm('users.can_block_users')):
            self.message_user(request, 'У вас нет прав на разблокировку пользователей', level='ERROR')
            return
        updated = queryset.update(is_blocked=False)
        self.message_user(request, f'Разблокировано {updated} пользователей(я)')

    unblock_users.short_description = 'Разблокировать выбранных пользователей'

    def activate_users(self, request, queryset):
        """Активировать выбранных пользователей"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} пользователей(я)')

    activate_users.short_description = 'Активировать выбранных пользователей'

    def deactivate_users(self, request, queryset):
        """Деактивировать выбранных пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {updated} пользователей(я)')

    deactivate_users.short_description = 'Деактивировать выбранных пользователей'