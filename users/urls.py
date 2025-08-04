from django.urls import path
from . import views


urlpatterns = [
    path("login/", views.login),
    path("refresh_token/", views.customTokenRefreshView.as_view()),
    path("register/", views.register),
    path("register/", views.register),
    path("logout/", views.logout),
    path("get_authentication/", views.get_authentication),
    path("change_password", views.change_password),
    path("request_password_reset/", views.reset_password_request_email),
    path("reset_password_request/", views.reset_password_request)
]
