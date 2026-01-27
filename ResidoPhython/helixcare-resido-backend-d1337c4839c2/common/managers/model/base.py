"""
Base Manager

To be inheritted by Other Model Managers to use the already declared
ready-to-use functions for filtering, ordering etc.
"""


class BaseModelManager:
    initialized = False
    model = None

    def __init__(self, **kwargs):
        if self.initialized:
            return
        if not self.model:
            raise NotImplementedError("Model class is not set for the Manager")
        self.initialized = True

    @classmethod
    def filter_by(cls, **kwargs):
        return cls.model.objects.filter(**kwargs)

    @classmethod
    def get_by(cls, **kwargs):
        return cls.model.objects.get(**kwargs)

    @classmethod
    def create_object(cls, **kwargs):
        return cls.model.objects.create(**kwargs)

    @classmethod
    def get_all(cls):
        return cls.model.objects.all()

    @classmethod
    def update_all(cls, objs, fields):
        return cls.model.objects.bulk_update(objs, fields)

    @classmethod
    def get_or_create(cls, **kwargs):
        return cls.model.objects.get_or_create(**kwargs)
