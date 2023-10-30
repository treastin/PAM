from django.core.mail import send_mail
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.users.models import UserVerification


@receiver(pre_save, sender=UserVerification)
def send_verification_code_to_user_email(sender, instance, *args, **kwargs):
    if instance.is_registration:
        mail_subject = 'PAM - Verify your account '
        mail_message = f'Here is your verification code for registration : {instance.code}'
    else:
        mail_subject = 'PAM - Password reset. '
        mail_message = f'Here is your verification code for password reset : {instance.code}'

    send_mail(
        mail_subject,
        mail_message,
        from_email=None,
        recipient_list=[instance.user.email],
        fail_silently=True
    )