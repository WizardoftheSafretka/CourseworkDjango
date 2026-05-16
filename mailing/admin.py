from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mailing.models import Recipient, Message, Mailing, AttemptMailing


class OwnerFilter(admin.SimpleListFilter):
    """Кастомный фильтр для владельца"""
    title = 'владелец'
    parameter_name = 'owner'

    def lookups(self, request, model_admin):
        if request.user.is_superuser or request.user.has_perm('mailing.view_all_mailings'):
            from users.models import User
            return [(user.id, user.email) for user in User.objects.all()]
        return [(request.user.id, request.user.email)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(owner_id=self.value())
        return queryset


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'last_name', 'first_name', 'owner', 'comment')
    list_filter = ('owner',)
    search_fields = ('email', 'last_name', 'first_name', 'middle_name', 'comment')

    def get_queryset(self, request):
        """Пользователи видят только своих получателей, менеджеры - всех"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('mailing.view_all_mailings'):
            return qs
        return qs.filter(owner=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор владельца"""
        if db_field.name == "owner":
            if request.user.is_superuser:
                kwargs["queryset"] = User.objects.all()
            else:
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Автоматически назначаем владельца"""
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'text_preview')
    list_filter = ('owner',)
    search_fields = ('title', 'text')

    def get_queryset(self, request):
        """Пользователи видят только свои сообщения, менеджеры - все"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('mailing.view_all_mailings'):
            return qs
        return qs.filter(owner=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор владельца"""
        if db_field.name == "owner":
            if request.user.is_superuser:
                kwargs["queryset"] = User.objects.all()
            else:
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Автоматически назначаем владельца"""
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Текст (предпросмотр)'


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'start_time', 'end_time', 'owner', 'disabled_by_manager', 'message_preview')
    list_filter = ('status', 'owner', 'disabled_by_manager', 'start_time', 'end_time')
    search_fields = ('name', 'message__title', 'recipients__email')
    filter_horizontal = ('recipients',)
    readonly_fields = ('status',)

    def get_queryset(self, request):
        """Пользователи видят только свои рассылки, менеджеры - все"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('mailing.view_all_mailings'):
            return qs
        return qs.filter(owner=request.user)

    def get_fieldsets(self, request, obj=None):
        """Менеджеры не могут редактировать владельца"""
        if request.user.is_superuser:
            return (
                ('Основная информация', {'fields': ('name', 'message', 'recipients', 'owner')}),
                ('Время рассылки', {'fields': ('start_time', 'end_time')}),
                ('Статус и управление', {'fields': ('status', 'disabled_by_manager')}),
            )
        elif request.user.has_perm('mailing.disable_mailings'):
            # Менеджеры видят все поля, но не могут менять владельца
            fields = ('name', 'message', 'recipients', 'start_time', 'end_time', 'status', 'disabled_by_manager')
            if obj and obj.owner:
                return (('Основная информация', {'fields': fields}),)
            return (('Основная информация', {'fields': fields}),)
        else:
            # Обычные пользователи
            return (
                ('Основная информация', {'fields': ('name', 'message', 'recipients')}),
                ('Время рассылки', {'fields': ('start_time', 'end_time')}),
            )

    def get_readonly_fields(self, request, obj=None):
        """Настраиваем readonly поля в зависимости от роли"""
        readonly = super().get_readonly_fields(request, obj)
        if request.user.has_perm('mailing.disable_mailings') and not request.user.is_superuser:
            # Менеджеры не могут менять владельца
            return readonly + ('owner',)
        if not request.user.is_superuser and not request.user.has_perm('mailing.disable_mailings'):
            # Обычные пользователи не могут менять статус и отключение
            return readonly + ('status', 'disabled_by_manager')
        return readonly

    def get_actions(self, request):
        """Настраиваем доступные действия"""
        actions = super().get_actions(request)
        if not request.user.has_perm('mailing.disable_mailings'):
            actions.pop('disable_mailings', None)
            actions.pop('enable_mailings', None)
        return actions

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор владельца и сообщения"""
        if db_field.name == "owner":
            if request.user.is_superuser:
                kwargs["queryset"] = User.objects.all()
            else:
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user.id
        elif db_field.name == "message":
            # Пользователи видят только свои сообщения
            if not (request.user.is_superuser or request.user.has_perm('mailing.view_all_mailings')):
                kwargs["queryset"] = Message.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Автоматически назначаем владельца"""
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def message_preview(self, obj):
        return obj.message.title if obj.message else 'Нет сообщения'

    message_preview.short_description = 'Сообщение'

    actions = ['disable_mailings', 'enable_mailings']

    def disable_mailings(self, request, queryset):
        """Отключение рассылок (доступно менеджерам)"""
        if not request.user.has_perm('mailing.disable_mailings'):
            self.message_user(request, 'У вас нет прав на отключение рассылок', level='ERROR')
            return
        for mailing in queryset:
            mailing.disable_by_manager()
        self.message_user(request, f'Отключено {queryset.count()} рассылок(и)')

    disable_mailings.short_description = 'Отключить выбранные рассылки'

    def enable_mailings(self, request, queryset):
        """Включение рассылок (доступно менеджерам)"""
        if not request.user.has_perm('mailing.disable_mailings'):
            self.message_user(request, 'У вас нет прав на включение рассылок', level='ERROR')
            return
        for mailing in queryset:
            mailing.enable_by_manager()
        self.message_user(request, f'Включено {queryset.count()} рассылок(и)')

    enable_mailings.short_description = 'Включить выбранные рассылки'


@admin.register(AttemptMailing)
class AttemptMailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt_time', 'status', 'mailing', 'server_response_preview')
    list_filter = ('status', 'attempt_time', 'mailing')
    search_fields = ('server_response', 'mailing__name')
    readonly_fields = ('attempt_time',)

    def get_queryset(self, request):
        """Ограничиваем доступ к попыткам рассылок"""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('mailing.view_all_mailings'):
            return qs
        return qs.filter(mailing__owner=request.user)

    def server_response_preview(self, obj):
        if obj.server_response:
            return obj.server_response[:50] + '...' if len(obj.server_response) > 50 else obj.server_response
        return '-'

    server_response_preview.short_description = 'Ответ сервера (предпросмотр)'