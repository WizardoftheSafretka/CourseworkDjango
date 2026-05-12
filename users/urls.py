from django.contrib.auth.views import LoginView, LogoutView
from users.views import UserCreateView, email_verification
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = "users"
urlpatterns = [
    path('login/', LoginView.as_view(template_name = 'login.html'), name = 'login'),
    path('logout/', LogoutView.as_view(next_page='main'), name = 'logout'),
    path('register/', UserCreateView.as_view(), name = 'register'),
    path('email_confirm/<str:token>/', email_verification, name='email_confirm'),
]