import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        username = uuid.uuid4().hex[:20]
        while CustomUser.objects.filter(username=username):
            username = uuid.uuid4().hex[:25]

        return self._create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    other_service_id = models.CharField(max_length=100, blank=True, verbose_name='Airtable レコードID (other_service_id)', help_text='システムで使用します（通常、変更の必要はありません）。')

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        if self.first_name == '' and self.last_name == '':
            return self.username
        else:
            return ' '.join([self.last_name, self.first_name])
