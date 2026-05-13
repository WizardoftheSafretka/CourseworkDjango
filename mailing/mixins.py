from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Mailing, Recipient


class ManagerRequiredMixin(UserPassesTestMixin):
    """Миксин: доступ только для менеджеров и администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
                self.request.user.is_manager or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас недостаточно прав для доступа к этой странице")
        return super().handle_no_permission()


class OwnerOrManagerMixin(UserPassesTestMixin):
    """Миксин: доступ владельцу или менеджеру"""

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        # Менеджеры имеют полный доступ
        if user.is_manager or user.is_superuser:
            return True

        # Проверяем владельца для модели Mailing
        if hasattr(self, 'get_mailing'):
            mailing = self.get_mailing()
            return mailing.owner == user

        # Проверяем владельца для модели Recipient
        if hasattr(self, 'get_recipient'):
            recipient = self.get_recipient()
            return recipient.owner == user

        return False

    def get_mailing(self):
        mailing_id = self.kwargs.get('pk') or self.kwargs.get('mailing_id')
        return get_object_or_404(Mailing, pk=mailing_id)

    def get_recipient(self):
        recipient_id = self.kwargs.get('pk') or self.kwargs.get('recipient_id')
        return get_object_or_404(Recipient, pk=recipient_id)


class UserNotBlockedMixin(UserPassesTestMixin):
    """Миксин: пользователь не должен быть заблокирован"""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and not user.is_blocked


class OwnerQuerysetMixin:
    """Миксин: автоматическая фильтрация по владельцу"""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_manager or user.is_superuser:
            return queryset

        return queryset.filter(owner=user)