# services/mailing_service.py
import logging

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import AttemptMailing

logger = logging.getLogger(__name__)


def sending_mail(mailing):
    """
    Функция отправки рассылки
    """
    recipients = mailing.recipients.all()

    if not recipients.exists():
        return {
            'success': False,
            'message': 'Нет получателей для этой рассылки',
            'sent_count': 0,
            'failed_count': 0,
            'can_send': False
        }

    now = timezone.now()
    if now < mailing.start_time or now > mailing.end_time:
        return {
            'success': False,
            'message': f'Время отправки вне разрешенного диапазона. Разрешенный период: с {mailing.start_time.strftime("%d.%m.%Y %H:%M")} по {mailing.end_time.strftime("%d.%m.%Y %H:%M")}',
            'sent_count': 0,
            'failed_count': 0,
            'can_send': False
        }

    if mailing.status != 'RUN':
        return {
            'success': False,
            'message': f'Рассылка имеет статус "{mailing.get_status_display()}". Для отправки требуется статус "Запущена"',
            'sent_count': 0,
            'failed_count': 0,
            'can_send': False
        }

    msg_title = mailing.message.title
    msg_text = mailing.message.text
    from_email = settings.EMAIL_HOST_USER

    sent_count = 0
    failed_count = 0
    errors = []

    for recipient in recipients:
        try:
            result = send_mail(
                msg_title,
                msg_text,
                from_email,
                [recipient.email],
                fail_silently=False,
            )

            if result == 1:
                AttemptMailing.objects.create(
                    status=AttemptMailing.SUCCESS,
                    server_response="Письмо успешно отправлено",
                    mailing=mailing
                )
                sent_count += 1
                logger.info(f"Письмо отправлено получателю {recipient.email}")
            else:
                error_msg = "Письмо не было отправлено"
                AttemptMailing.objects.create(
                    status=AttemptMailing.FAILED,
                    server_response=error_msg,
                    mailing=mailing
                )
                failed_count += 1
                errors.append(f"{recipient.email}: {error_msg}")

        except Exception as e:
            error_msg = str(e)
            AttemptMailing.objects.create(
                status=AttemptMailing.FAILED,
                server_response=error_msg,
                mailing=mailing
            )
            failed_count += 1
            errors.append(f"{recipient.email}: {error_msg}")
            logger.error(f"Ошибка отправки письма {recipient.email}: {error_msg}")

    if sent_count == recipients.count() and sent_count > 0:
        mailing.status = 'completed'
        mailing.save(update_fields=['status'])

    return {
        'success': failed_count == 0,
        'message': f'Отправлено: {sent_count}, Ошибок: {failed_count}',
        'sent_count': sent_count,
        'failed_count': failed_count,
        'errors': errors[:5],
        'can_send': True
    }