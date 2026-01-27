from lookup.fields import BaseSerializer
from .models import (
    NotificationDLFile,
    NotificationQueue,
    NotificationSetting,
    NotificationMessage,
    NotificationDL,
    NotificationTemplate,
    NotificationUserDL,
)
from rest_framework import serializers


class NotificationQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationQueue
        fields = "__all__"


class NotificationSettingSerializer(BaseSerializer):
    class Meta:
        model = NotificationSetting
        fields = "__all__"


class NotificationDLFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDLFile
        fields = "__all__"


class NotificationDLSerializer(BaseSerializer):
    class Meta:
        model = NotificationDL
        fields = "__all__"


class NotificationUserDLSerializer(BaseSerializer):
    class Meta:
        model = NotificationUserDL
        fields = "__all__"


class NotificationTemplateSerializer(BaseSerializer):
    class Meta:
        model = NotificationTemplate
        fields = "__all__"


class NotificationMessageSerializer(BaseSerializer):
    class Meta:
        model = NotificationMessage
        fields = "__all__"
