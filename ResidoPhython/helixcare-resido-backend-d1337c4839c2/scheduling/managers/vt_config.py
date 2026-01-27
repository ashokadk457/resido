from common.managers.model.base import BaseModelManager
from scheduling.models import StaffVisitTypeConfiguration


class VisitTypeConfigManager(BaseModelManager):
    model = StaffVisitTypeConfiguration

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.staff_id = kwargs.get("staff_id")
        self.staff_ids = kwargs.get("staff_ids")
        self.visit_type = kwargs.get("visit_type")
        self.find_all_vt_configs = kwargs.get("get_all_vt_configs")

        # Computation values
        self.vt_config = self.get_visit_type_config()
        self.all_vt_configs = (
            self.get_all_vt_configs() if self.find_all_vt_configs else []
        )

        # Bulk or multi-staff computation values
        self.multi_staff_vt_configs_map, self.multi_staff_all_vt_configs_map = {}, {}
        if self.find_all_vt_configs:
            self.multi_staff_all_vt_configs_map = (
                self.get_multi_staff_all_vt_configs_map()
                if self.find_all_vt_configs
                else {}
            )
        else:
            self.multi_staff_vt_configs_map = self.get_multi_staff_vt_configs_map()

    def _get_visit_type_configs(self, staff_ids):
        return self.filter_by(staff_id__in=staff_ids, visit_type=self.visit_type)

    def get_visit_type_config(self):
        if not self.staff_id:
            return

        vt_configs = self._get_visit_type_configs(staff_ids=[self.staff_id])
        return vt_configs.first()

    @classmethod
    def _build_multi_staff_vt_config_map(cls, vt_configs):
        multi_staff_vt_configs_map = {}
        for vt_config in vt_configs:
            multi_staff_vt_configs_map[
                str(vt_config.staff_id)
            ] = multi_staff_vt_configs_map.get(str(vt_config.staff_id), []) + [
                vt_config
            ]

        return multi_staff_vt_configs_map

    def get_multi_staff_vt_configs_map(self):
        if not self.staff_ids:
            return {}

        vt_configs = self._get_visit_type_configs(staff_ids=self.staff_ids)
        return self._build_multi_staff_vt_config_map(vt_configs=vt_configs)

    def _get_all_vt_configs(self, staff_ids):
        return self.filter_by(staff_id__in=staff_ids)

    def get_all_vt_configs(self):
        if not self.staff_id:
            return

        return self._get_all_vt_configs(staff_ids=[self.staff_id])

    def get_multi_staff_all_vt_configs_map(self):
        if not self.staff_ids:
            return {}

        all_vt_configs = self._get_all_vt_configs(staff_ids=self.staff_ids)
        return self._build_multi_staff_vt_config_map(vt_configs=all_vt_configs)

    def get_staff_vt_config(self, staff_id):
        if not staff_id:
            return

        if staff_id == self.staff_id:
            return self.vt_config

        return self.multi_staff_vt_configs_map.get(str(staff_id))

    def get_staff_vt_config_duration(self, staff_id):
        if not staff_id:
            return

        vt_config = self.get_staff_vt_config(staff_id=staff_id)
        return vt_config.duration

    def get_staff_all_vt_configs(self, staff_id):
        if not staff_id:
            return []

        if self.staff_id == staff_id:
            return self.all_vt_configs

        return self.multi_staff_all_vt_configs_map.get(str(staff_id), [])
