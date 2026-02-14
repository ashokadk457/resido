from common.models import HealthCareCustomer
from common.utils.enum import EnumWithValueConverter
from lookup.models import Lookup
from helixauth.models import (
    Entity,
    EntityAttributeComposition,
)


class CachedModel(EnumWithValueConverter):
    _LOOKUP = Lookup
    _PERM_ENTITY = Entity
    _PERM_ENTITY_ATTR_COMP = EntityAttributeComposition
    _TENANT = HealthCareCustomer
