from django.urls import path

from .views import *

urlpatterns = [
    path('site/information/', site_information, name='site_information'),
    path('user/profile/', user_profile, name='user_profile'),
    path('user/todays_entry_status/', todays_entry_status, name='user_todays_entry_status'),
]
