from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', ]

    add_fieldsets = (
        (None, {
            'fields': ('username', 'email',)}
         ),
    )

    fieldsets = UserAdmin.fieldsets + (
        # ('Internal information', {
        ('内部情報', {
            'fields': ('other_service_id',)}
         ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
