from common.managers.model.generic import GenericModelManager


class UserRoleObjectManager(GenericModelManager):
    def create(self, **kwargs):
        reference_role = kwargs.pop("copy_from", None)
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, reference_role=reference_role)
        return obj
