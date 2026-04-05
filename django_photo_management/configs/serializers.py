from rest_framework import serializers

from .models import SystemConfig


class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = ('id', 'key', 'value', 'description')
