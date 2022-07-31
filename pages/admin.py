from django.contrib import admin
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from django.db.utils import ProgrammingError

from .models import *

# Register your models here.

try:
    current_site = Site.objects.get_current()
    # admin.site.site_title = current_site.name + ' administration'
    admin.site.site_title = current_site.name + ' サイト管理'
    # admin.site.site_header = current_site.name + ' administration'
    admin.site.site_header = current_site.name + ' 管理サイト'
except ProgrammingError:
    pass


class CustomSiteAdmin(SiteAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ChoiceQuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    exclude = ('answer_time_data',)

    def save_model(self, request, obj, form, change):
        obj.answer_time_data = []
        super().save_model(request, obj, form, change)


class InputQuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


class OptionAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


class AttendanceRecordAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('user', 'entry_time', 'leave_time', 'mental_score_at_entry', 'mental_score_at_leave', 'mental_rank_at_entry', 'mental_rank_at_leave', 'notes')
        }),
        # ('Internal information', {
        ('内部情報', {
            'fields': ('other_service_id',)
        })
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TemporaryQuestionSetAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('questions',),
            # 'description': 'This data is automatically managed by the system. Users generally cannot edit or delete these.'
            'description': 'このデータはシステムによって自動で管理されています。通常、ユーザーはこれらの編集や削除を行うことはできません。'
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Site)
admin.site.register(Site, CustomSiteAdmin)
admin.site.register(ChoiceQuestion, ChoiceQuestionAdmin)
admin.site.register(InputQuestion, InputQuestionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(AttendanceRecord, AttendanceRecordAdmin)
admin.site.register(TemporaryQuestionSet, TemporaryQuestionSetAdmin)
