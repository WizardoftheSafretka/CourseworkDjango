import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from users.models import User


class Recipient(models.Model):
    email = models.EmailField(verbose_name="Email", help_text="Укажите email")
    last_name = models.CharField(
        max_length=50, verbose_name="Фамилия", help_text="Введите фамилию"
    )
    first_name = models.CharField(
        max_length=50, verbose_name="Имя", help_text="Введите имя"
    )
    middle_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Отчество",
        help_text="Введите отчество",
    )
    comment = models.TextField(
        verbose_name="комментарий",
        blank=True,
        null=True,
        help_text="Введите комментарий",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='владелец',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        unique_together = ['email', 'owner']

    def __str__(self):
        return self.email


class Message(models.Model):
    title = models.CharField(
        max_length=50, verbose_name="Тема письма", help_text="Введите тему письма"
    )
    text = models.TextField(
        verbose_name="текст письма", help_text="Введите текст письма"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='сообщения',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("title",)
        # permissions = [
        #     ('can_unpublish_product', 'Can unpublish product')
        # ]

    def __str__(self):
        return self.title


class Mailing(models.Model):

    STATUS_CHOICES = [
        ("CREATED", "Создана"),
        ("RUN", "Запущена"),
        ("FINISHED", "Завершена"),
        ('turned-off', 'Отключена'),
    ]

    name = models.CharField('Название', max_length=200, help_text="Введите название рассылки")
    start_time = models.DateTimeField(
        verbose_name="Начало рассылки", help_text="Введите дату и время начала рассылки",
    )
    end_time = models.DateTimeField(
        verbose_name="Конец рассылки", help_text="Введите дату и время конца рассылки"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус рассылки"
    )
    message = models.ForeignKey(
        "Message",
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="сообщение",
    )
    recipients = models.ManyToManyField(Recipient)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='владелец',
        blank=True,
        null=True,
    )
    disabled_by_manager = models.BooleanField(default=False, verbose_name='отключена менеджером')

    class Meta:
        verbose_name = 'рассылка'
        verbose_name_plural = 'рассылки'
        permissions = [
            ("view_all_mailings", "Может просматривать все рассылки"),
            ("disable_mailings", "Может отключать рассылки"),
        ]


    def disable_by_manager(self):
        """Отключение рассылки менеджером"""

        self.disabled_by_manager = True
        self.status = 'turned-off'
        self.save()


    def enable_by_manager(self):
        """Включение рассылки менеджером"""

        self.disabled_by_manager = False
        if self.status == 'turned-off':
            self.status = 'created'
        self.save()

    def update_status(self):
        """Метод обновления статуса"""

        now_time = timezone.now()
        old_status = self.status

        if now_time < self.start_time:
            new_status = "CREATED"

        elif now_time <= self.start_time < self.end_time:
            new_status = "RUN"

        elif now_time >= self.end_time:
            new_status = "FINISHED"

        else:
            new_status = self.status

        if old_status != new_status:
            self.status = new_status

        self.save()

        return self.status



    def __str__(self):
        return f'{self.name} - {self.status}'


class AttemptMailing(models.Model):
    """Модель попытки рассылки"""

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Успешно'
        FAILED = 'failed', 'Не успешно'

    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='время попытки'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.FAILED,
        verbose_name='статус'
    )
    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='ответ почтового сервера'
    )
    mailing = models.ForeignKey(
        "Mailing",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attempts',
        verbose_name='рассылка'
    )

    class Meta:
        verbose_name = 'попытка'
        verbose_name_plural = 'попытки'
        ordering = ['-attempt_time', 'status']

    def __str__(self):
        return f"Попытка от {self.attempt_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.get_status_display()}"



