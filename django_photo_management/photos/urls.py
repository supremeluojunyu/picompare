from django.urls import path
from rest_framework.routers import DefaultRouter

from .superuser_crypto import (
    SuperuserCryptoExportView,
    SuperuserCryptoRevealView,
    SuperuserCryptoSaveKeyView,
    SuperuserCryptoStatusView,
)
from .views import PhotoUploadViewSet

router = DefaultRouter()
router.register(r'', PhotoUploadViewSet, basename='photo')
urlpatterns = [
    path('superuser_crypto/status/', SuperuserCryptoStatusView.as_view(), name='superuser_crypto_status'),
    path('superuser_crypto/save_key/', SuperuserCryptoSaveKeyView.as_view(), name='superuser_crypto_save_key'),
    path('superuser_crypto/reveal/', SuperuserCryptoRevealView.as_view(), name='superuser_crypto_reveal'),
    path('superuser_crypto/export/', SuperuserCryptoExportView.as_view(), name='superuser_crypto_export'),
] + router.urls
