from common.constants import CategoryForVisitType
from common.managers.model.base import BaseModelManager
from lookup.models import Lookup
from scheduling.models import VisitTypeCategory


class VTCategoryManager(BaseModelManager):
    model = VisitTypeCategory

    @classmethod
    def populate_default_categories(cls, **kwargs):
        all_visit_types = [
            c.get("code")
            for c in Lookup.objects.filter(name="VISIT_TYPE").values("code")
        ]
        categorised_objs = []
        for visit_type in all_visit_types:
            category = (
                CategoryForVisitType.returning_patient.value
                if "EST" in visit_type
                else CategoryForVisitType.new_patient.value
            )
            vt_category_obj = cls.model(visit_type=visit_type, category=category)
            categorised_objs.append(vt_category_obj)

        cls.model.objects.bulk_create(categorised_objs)
