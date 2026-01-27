from common.managers.model.base import BaseModelManager
from residents.models import ResidentFamily


class PatientFamilyManager(BaseModelManager):
    model = ResidentFamily

    @classmethod
    def get_patient_family_relations(cls, patient):
        return cls.model.objects.filter(patient=patient).select_related("member")
