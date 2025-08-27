from django.urls import path
from . import views


urlpatterns = [
    path("login/", views.login),
    path("refresh_token/", views.customTokenRefreshView.as_view()),
    path("register/", views.register),
    path("logout/", views.logout),
    path("get_authentication/", views.get_authentication),
    path("change_password/", views.change_password),
    path("request_password_reset/", views.reset_password_request_email),
    path("reset_password_request/", views.reset_password_request),
    path("onboarding/", views.onboarding),
    path("get_skills/", views.get_user_skills),
    path("skills/", views.all_skills),
    path("me/", views.get_user),
    path("me/quiz/", views.get_user_quiz),
    path("all_questions/", views.get_all_questions),
    path("submit-quiz/", views.submit_quiz),
    path("get_user_quiz_results/", views.get_user_quiz_results),
    path("get_quiz/", views.get_quiz),
]
