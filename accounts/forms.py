from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_('email address'), help_text='この項目は必須です。')
    password1 = forms.CharField(required=False)
    password2 = forms.CharField(required=False)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email',)


class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ('username', 'last_name', 'first_name',)


class LimitedUserChangeForm(CustomUserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = 'readonly'
        self.fields['username'].help_text += '（この項目はサービス管理者によって変更が禁止されています）'
