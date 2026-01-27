import yaml

from common.managers.model.base import BaseModelManager
from helixauth.models import Module
from helixauth.serializers import ModuleSerializer


class ModuleManager(BaseModelManager):
    model = Module

    def get_serialized_modules(self, qs=None):
        if qs is None:
            qs = self.model.objects.all()
        return ModuleSerializer(qs, many=True).data

    @classmethod
    def seed_modules(cls):
        with open("data/permissions/modules.yaml", "r") as yaml_file:
            file_data = yaml.load_all(yaml_file, yaml.BaseLoader)
            for data in file_data:
                obj, _ = cls.model.objects.get_or_create(
                    code=data["code"], defaults=data
                )
