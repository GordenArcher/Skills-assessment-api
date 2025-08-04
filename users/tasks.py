from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from celery import shared_task
import requests
from django.conf import settings
import base64
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@shared_task
def send_verification_email(user_id):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_link = f"http://localhost:5173/verify-email/?uid={uid}&token={token}"

    html_content = render_to_string("Emails/verify_email.html", {
        "username": user.username,
        "verification_link": verification_link,
        "email": user.email
    })

    email = EmailMessage(
        subject="Verify Your Account",
        body=html_content,
        from_email="",
        to=[user.email],
    )
    email.content_subtype = "html"
    email.send()




@shared_task
def send_reset_password_request_email(user_id, email):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_link = f"http://localhost:5173/change-password/?uid={uid}&token={token}"

    html_content = render_to_string("Emails/ResetEmailRequest.html", {
        "verification_link": verification_link,
        "email": email
    })

    email = EmailMessage(
        subject="Reset Your password",
        body=html_content,
        to=[user.email],
    )
    email.content_subtype = "html"
    email.send()
