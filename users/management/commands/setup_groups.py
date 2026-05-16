from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import User
from mailing.models import Mailing


class Command(BaseCommand):
    help = 'Настройка групп и прав доступа'

    def handle(self, *args, **options):
        # Создаем группу "Менеджеры"
        managers_group, created = Group.objects.get_or_create(name='Менеджеры')

        # Получаем права
        content_type_user = ContentType.objects.get_for_model(User)
        content_type_mailing = ContentType.objects.get_for_model(Mailing)

        # Права для менеджеров
        permissions = [
            ('can_view_all_users', content_type_user),
            ('can_block_users', content_type_user),
            ('view_all_mailings', content_type_mailing),
            ('disable_mailings', content_type_mailing),
        ]

        for codename, content_type in permissions:
            try:
                permission = Permission.objects.get(codename=codename, content_type=content_type)
                managers_group.permissions.add(permission)
                self.stdout.write(f'Добавлено право {codename}')
            except Permission.DoesNotExist:
                self.stdout.write(f'Право {codename} не найдено')

        self.stdout.write(self.style.SUCCESS('Группы и права успешно настроены'))