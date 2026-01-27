import os
import json
from datetime import datetime
from common.constants import (
    CUSTOM_READABLE_TIMESTAMP,
    UTC_TIMEZONE,
    DEFAULT_VERSIONS_DATA,
)
from common.utils.logging import logger


class ServiceManager:
    def get_service_info(self):
        versions_data = self.get_versions_data_from_env_var()
        if versions_data:
            return versions_data

        versions_data = self.get_base_versions_data_from_versions_file()
        if versions_data:
            return versions_data

        return DEFAULT_VERSIONS_DATA

    @classmethod
    def get_versions_data_from_env_var(cls):
        service_version_info_data_from_env = os.environ.get("SERVICE_INFO")
        if not service_version_info_data_from_env:
            return service_version_info_data_from_env

        try:
            service_version_info_data_from_env = json.loads(
                service_version_info_data_from_env
            )
            deployed_on = service_version_info_data_from_env.get("deployed_on")
            deployed_on_dt = datetime.strptime(
                deployed_on[:-4], "%d %b %Y %H:%M:%S.%f"
            ).astimezone(tz=UTC_TIMEZONE)
            uptime = datetime.now().astimezone(tz=UTC_TIMEZONE) - deployed_on_dt
            service_version_info_data_from_env["uptime"] = uptime.seconds
        except Exception as e:
            logger.error(
                f"Exception occurred while getting versions data from env vars: {str(e)}"
            )
            return None

        return service_version_info_data_from_env

    def get_base_versions_data_from_versions_file(self):
        raw_versions_data = self.read_versions_file()
        base_versions_data = self.format_raw_versions_data(
            raw_versions_data=raw_versions_data
        )
        if "deployed_on" not in base_versions_data:
            base_versions_data["deployed_on"] = None
        if "uptime" not in base_versions_data:
            base_versions_data["uptime"] = None
        return base_versions_data

    @classmethod
    def read_versions_file(cls):
        try:
            with open("common/version.txt", "r") as f:
                raw_versions_data = f.read()
            return raw_versions_data
        except Exception as e:
            logger.error(f"Exception occurred while reading versions data: {str(e)}")
            return ""

    @staticmethod
    def format_raw_versions_data(raw_versions_data):
        if not raw_versions_data:
            return DEFAULT_VERSIONS_DATA

        try:
            return dict(
                [info.split("=") for info in raw_versions_data.split("\n") if info]
            )
        except Exception as e:
            logger.error(f"Exception occurred while formatting versions data: {str(e)}")
        return DEFAULT_VERSIONS_DATA

    def set_service_info_in_env_var(self):
        base_versions_data = self.get_base_versions_data_from_versions_file()
        deployed_on = (
            datetime.now()
            .astimezone(tz=UTC_TIMEZONE)
            .strftime(CUSTOM_READABLE_TIMESTAMP)
        )
        final_versions_data_to_set = {**base_versions_data, "deployed_on": deployed_on}

        try:
            os.environ.setdefault(
                "SERVICE_INFO", json.dumps(final_versions_data_to_set)
            )
        except Exception as e:
            logger.error(
                f"Exception occurred while setting versions data in env var: {str(e)}"
            )
