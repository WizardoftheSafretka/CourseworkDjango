from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name='Телефон', help_text='Введите номер телефона')
    token = models.CharField(max_length=100, verbose_name='Token', blank=True, null=True)
    is_blocked = models.BooleanField(default=False, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email

    permissions = [
        ("can_view_all_users", "Может просматривать всех пользователей"),
        ("can_block_users", "Может блокировать пользователей"),
    ]

    @property
    def is_manager(self):
        """Проверка, является ли пользователь менеджером"""
        return self.groups.filter(name='Менеджеры').exists() or self.is_staff