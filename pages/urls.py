from django.urls import path

from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('terms', terms, name='terms'),
    path('privacy_policy', privacy_policy, name='privacy_policy'),
    path('s/my_report', my_report, name='s_my_report'),
    path('s/view_records', view_records, name='s_view_records'),
    path('s/entry_description', entry_description, name='s_entry_description'),
    path('s/entry', entry, name='s_entry'),
    path('s/leave_description', leave_description, name='s_leave_description'),
    path('s/leave', leave, name='s_leave'),
]
