from rest_framework import serializers

from processflow.constants import ProcessStatus
from processflow.models import Process


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        exclude = ["version", "raw_payload"]

    def get_raw_payload(self):
        if self.instance.status == ProcessStatus.COMPLETED.value:
            return None
        return self.instance.raw_payload


class ProcessTrimmedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        exclude = [
            "raw_payload",
            "version",
        ]
