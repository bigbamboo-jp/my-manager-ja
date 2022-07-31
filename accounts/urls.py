from django.urls import path

from .views import *

urlpatterns = [
    path('user_information/', user_information_change, name='user_information_change'),
    path('issue_tokens/', issue_tokens, name='issue_tokens'),
]
