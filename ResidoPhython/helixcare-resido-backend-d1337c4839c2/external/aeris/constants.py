import os

from common.utils.enum import EnumWithValueConverter

AERIS_URL = os.getenv("AERIS_URL", "https://xchange.qa.helixbeat.com")
AERIS_LOGIN_EMAIL = os.getenv("AERIS_LOGIN_EMAIL", "system.user2@xchange.com")
AERIS_LOGIN_PASSWORD = os.getenv("AERIS_LOGIN_PASSWORD", "User2@Xchange")
AERIS_CUSTOMER_ID = os.getenv(
    "AERIS_CUSTOMER_ID", "b5c80bed-1178-4f53-873a-c826632d3bd2"
)
AERIS_JSON_TO_FHIR_PATIENT_PIPELINE_ID = os.getenv(
    "AERIS_JSON_TO_FHIR_PATIENT_PIPELINE_ID", "ca874997-b083-4c29-b9be-e808964a8261"
)
AERIS_JSON_TO_FHIR_DOCREF_PIPELINE_ID = os.getenv(
    "AERIS_JSON_TO_FHIR_DOCREF_PIPELINE_ID", "50b0bd92-8925-46fe-a9da-e16cb37e79c0"
)


class PipelineExecutionMode(EnumWithValueConverter):
    REALTIME = "realtime"
    BATCH = "batch"
