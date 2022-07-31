from allauth.account.models import EmailAddress
from allauth.account.signals import password_reset
from django.dispatch import receiver
from django.conf import settings


@receiver(password_reset)
def auto_verify_email_address_on_password_reset(sender, request, user, **kwargs):
    if getattr(settings, 'AUTO_VERIFY_EMAIL_ADDRESS_ON_PASSWORD_RESET', 'Django') == True:
        user_email_address = EmailAddress.objects.get(user=user, email=user.email)
        if user_email_address.verified == False:
            user_email_address.verified = True
            user_email_address.save()
