from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (TokenBlacklistView,
                                            TokenRefreshView, TokenVerifyView)

urlpatterns = [
    # セキュリティフラグ：未変更
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/v1/', include('api.urls')),
    path('', include('pages.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
