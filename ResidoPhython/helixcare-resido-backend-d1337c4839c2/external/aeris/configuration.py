from external.aeris.constants import (
    AERIS_URL,
    AERIS_LOGIN_EMAIL,
    AERIS_LOGIN_PASSWORD,
    AERIS_CUSTOMER_ID,
    AERIS_JSON_TO_FHIR_DOCREF_PIPELINE_ID,
    AERIS_JSON_TO_FHIR_PATIENT_PIPELINE_ID,
)


class AERISConfiguration:
    @classmethod
    def init(cls):
        # TODO put a null safe check to see if the configuration is present in the env var

        return cls()

    def __init__(self):
        self.url = AERIS_URL
        self.login_email = AERIS_LOGIN_EMAIL
        self.login_password = AERIS_LOGIN_PASSWORD
        self.customer_id = AERIS_CUSTOMER_ID
        self.json_to_fhir_docref_pipeline_id = AERIS_JSON_TO_FHIR_DOCREF_PIPELINE_ID
        self.json_to_fhir_patient_pipeline_id = AERIS_JSON_TO_FHIR_PATIENT_PIPELINE_ID
