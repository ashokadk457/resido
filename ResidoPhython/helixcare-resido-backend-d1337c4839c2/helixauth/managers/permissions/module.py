from common.managers.model.base import BaseModelManager
from helixauth.models import ModulePermission


class ModulePermissionManager(BaseModelManager):
    model = ModulePermission
