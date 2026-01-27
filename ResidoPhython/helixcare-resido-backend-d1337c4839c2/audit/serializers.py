from rest_framework import serializers

from residents.models import Resident
from residents.serializers import ResidentSerializer
from staff.models import HelixStaff
from staff.serializers import StaffSerializer
from .models import AuditEvent, Audit


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audit
        fields = [
            "event",
            "old_value",
            "new_value",
            "field",
        ]


class AuditEventListSerializer(serializers.ModelSerializer):
    audits = AuditSerializer(source="audit_set.all", many=True, required=False)
    user_info = serializers.SerializerMethodField()
    action_detail = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "created_on",
            "table",
            "key",
            "action",
            "created_by",
            "ip_address",
            "module",
            "audits",
            "user_info",
            "action_detail",
        ]

    @staticmethod
    def get_user_info(obj):
        if obj.created_by is None:
            return None

        match = None
        try:
            match = HelixStaff.objects.get(user__id=obj.created_by.id)
            return StaffSerializer(match).data
        except HelixStaff.DoesNotExist:
            pass

        if match is None:
            try:
                match = Resident.objects.get(user__id=obj.created_by.id)
                return ResidentSerializer(match).data
            except Resident.DoesNotExist:
                pass
        return None

    @staticmethod
    def get_action_detail(obj):
        if obj.action and obj.table:
            return f"{obj.action} {obj.table}"
        return None


class AuditEventDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = "__all__"
