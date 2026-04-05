import base64

from rest_framework import serializers

from .models import PendingConfirmation


class PendingSerializer(serializers.ModelSerializer):
    original_image_base64 = serializers.SerializerMethodField()
    adjusted_image_base64 = serializers.SerializerMethodField()

    class Meta:
        model = PendingConfirmation
        fields = (
            'id',
            'person_number',
            'adjust_reason',
            'original_image_base64',
            'adjusted_image_base64',
        )

    def get_original_image_base64(self, obj):
        return base64.b64encode(bytes(obj.original_image)).decode('ascii')

    def get_adjusted_image_base64(self, obj):
        return base64.b64encode(bytes(obj.adjusted_image)).decode('ascii')
