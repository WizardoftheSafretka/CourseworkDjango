import secrets

from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from django.contrib import messages

from config.settings import EMAIL_HOST_USER
from users.forms import UserRegisterForm
from users.models import User


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.token = secrets.token_hex(16)
        user.save()

        host = self.request.get_host()
        url = f'http://{host}/users/email_confirm/{user.token}/'

        try:
            send_mail(
                subject='Подтверждение почты',
                message=f'Привет! Перейди по ссылке для подтверждения почты: {url}',
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Ошибка отправки письма: {e}")
            messages.error(self.request, "Ошибка при отправке письма. Попробуйте позже.")
            return redirect("users:register")

        messages.success(self.request, "Письмо с подтверждением отправлено на вашу почту.")
        return super().form_valid(form)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)

    if user.is_active:
        messages.info(request, "Аккаунт уже активирован. Войдите в систему.")
        return redirect(reverse("users:login"))

    user.is_active = True
    user.token = None
    user.save()

    messages.success(request, "Почта подтверждена! Теперь вы можете войти.")
    return redirect(reverse("users:login"))


class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    html_email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Инструкция по восстановлению пароля отправлена на указанный email.'
        )
        return response

    def form_invalid(self, form):
        for error in form.errors.get('email', []):
            messages.error(self.request, error)
        return super().form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Пароль успешно изменён! Теперь вы можете войти с новым паролем.'
        )
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_url'] = reverse_lazy('login')
        return context


@csrf_exempt
def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('mailing/main.html')
    else:
        form = AuthenticationForm()

    return render(request, 'mailing/login.html', {'form': form})