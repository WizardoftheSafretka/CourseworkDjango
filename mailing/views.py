from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin, TemplateView

from mailing.forms import RecipientForm, MessageForm, MailingForm
from mailing.models import Recipient, Message, Mailing, AttemptMailing
from mailing.services import sending_mail


class RecipientListView(ListView):
    model = Recipient
    context_object_name = "recipients"


class RecipientDetailView(DetailView):
    model = Recipient


class RecipientCreateView(CreateView):
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy("mailing:recipient_list")



class RecipientUpdateView(UpdateView):
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy("mailing:recipient_list")

    def get_success_url(self):
        return reverse("mailing:recipient_detail", args=[self.kwargs.get("pk")])


class RecipientDeleteView(DeleteView):
    model = Recipient
    success_url = reverse_lazy("mailing:recipient_list")


class MessageListView(ListView):
    model = Message
    context_object_name = "messages"




class MessageDetailView(DetailView):
    model = Message


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")



class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    success_url = reverse_lazy("mailing:message_list")

    def get_success_url(self):
        return reverse("mailing:message_detail", args=[self.kwargs.get("pk")])


class MessageDeleteView(DeleteView):
    model = Message
    success_url = reverse_lazy("mailing:message_list")


class MailingListView(ListView):
    model = Mailing
    context_object_name = "mailings"

class MailingDetailView(DetailView):
    model = Mailing

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mailing = self.object
        context['now'] = timezone.now()
        can_send = (
                mailing.start_time <= timezone.now() <= mailing.end_time
        )
        context['can_send'] = can_send
        return context

    def post(self, request, *args, **kwargs):
        """
        Обработка POST запроса - запуск рассылки
        """
        self.object = self.get_object()
        mailing = self.object

        mailing.update_status()

        result = sending_mail(mailing)

        request.session['send_result'] = result

        if result['success']:
            messages.success(
                request,
                f"Рассылка успешно отправлена! {result['message']}"
            )
        else:
            if result.get('can_send') is False:
                messages.error(request, f"Нельзя отправить рассылку: {result['message']}")
            else:
                messages.warning(
                    request,
                    f"Рассылка отправлена с ошибками. {result['message']}"
                )
                for error in result.get('errors', [])[:3]:
                    messages.error(request, f"Ошибка: {error}")

        return redirect(reverse('mailing_detail', kwargs={'pk': mailing.pk}))

class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy("mailing:mailing_list")


class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy("mailing:mailing_list")

    def get_success_url(self):
        return reverse("mailing:mailing_detail", args=[self.kwargs.get("pk")])


class MailingDeleteView(DeleteView):
    model = Mailing
    success_url = reverse_lazy("mailing:mailing_list")

class AttemptMailingListView(ListView):
    model = AttemptMailing
    context_object_name = "attempts"


class MainView(ContextMixin, TemplateView):
    template_name = 'main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        context.update({
            'total_mailings': Mailing.objects.count(),
            'active_mailings': Mailing.objects.filter(
                start_time__lte=now, end_time__gte=now, status='started'
            ).count(),
            'unique_recipients': Recipient.objects.count(),
        })

        return context