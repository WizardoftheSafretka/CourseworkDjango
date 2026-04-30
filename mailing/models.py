from django.db import models


class MailingRecipient(models.Model):
    email = models.EmailField(verbose_name='Email', help_text='Укажите email')
    last_name = models.CharField(max_length=50,verbose_name='Фамилия', help_text='Введите фамилию')
    first_name = models.CharField(max_length=50,verbose_name='Имя', help_text='Введите имя')
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='Отчество', help_text='Введите отчество')
    comment = models.TextField(verbose_name='комментарий', blank=True, null=True, help_text='Введите комментарий')

    class Meta:
        verbose_name = 'Получатель рассылки'
        verbose_name_plural = 'Получатели рассылки'
        ordering = ('email',)
        # permissions = [
        #     ('can_unpublish_product', 'Can unpublish product')
        # ]

    def __str__(self):
        return self.email

class Message(models.Model):
    title = models.CharField(max_length=50, verbose_name='Тема письма', help_text='Введите тему письма')
    text = models.TextField(verbose_name='текст письма', help_text='Введите текст письма')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ('title',)
        # permissions = [
        #     ('can_unpublish_product', 'Can unpublish product')
        # ]

    def __str__(self):
        return self.title

class Mailing(models.Model):
    CREATED = 'created'
    RUN = 'run'
    FINISHED = 'finished'

    STATUS_CHOICES = [
        (CREATED, 'Создана'),
        (RUN, 'Запущена'),
        (FINISHED, 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name='Начало рассылки', help_text='Введите дату и время начала рассылки')
    end_time = models.DateTimeField(verbose_name='Конец рассылки', help_text='Введите дату и время конца рассылки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус рассылки')
    message = models.ForeignKey("Message", on_delete=models.CASCADE, related_name='messages', verbose_name='сообщение')
    recipients = models.ManyToManyField(MailingRecipient)
