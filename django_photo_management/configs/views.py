from rest_framework import permissions, viewsets

from .models import SystemConfig
from .serializers import ConfigSerializer


class ConfigViewSet(viewsets.ModelViewSet):
    queryset = SystemConfig.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [permissions.IsAdminUser]
