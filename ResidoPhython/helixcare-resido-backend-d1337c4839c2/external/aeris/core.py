from common.utils.requests import helix_request
from external.aeris.configuration import AERISConfiguration
from external.aeris.constants import PipelineExecutionMode


class AERIS:
    PIPELINE_RUN_ENDPOINT = (
        "/api/v1/customers/{customer_id}/pipelines/{pipeline_id}/run"
    )
    LOGIN_ENDPOINT = "/api/v1/user/login"
    UPLOAD_ENDPOINT = "/api/v1/upload-to-sftp"

    @classmethod
    def init(cls, config: AERISConfiguration):
        return cls(config=config)

    def __init__(self, config: AERISConfiguration):
        self.config = config
        self.auth_header = None
        self.token = None
        self.token = self.login()

    def login(self):
        if self.token:
            return

        url = f"{self.config.url}{self.LOGIN_ENDPOINT}"
        payload = {
            "email": self.config.login_email,
            "password": self.config.login_password,
        }
        response, _ = helix_request.post(url, json=payload)

        if response and response.status_code == 200:
            self.token = response.json()["data"]["access"]
            self.auth_header = f"Bearer {self.token}"

        return self.token

    def run_pipeline(
        self,
        pipeline_id,
        mode=PipelineExecutionMode.BATCH.value,
        input_data=None,
        push_to_destination=False,
    ):
        url = f"{self.config.url}{self.PIPELINE_RUN_ENDPOINT}"
        url = url.format(customer_id=self.config.customer_id, pipeline_id=pipeline_id)
        payload = {"process_type": mode}
        if mode == PipelineExecutionMode.REALTIME.value:
            payload["input_data"] = input_data
            payload["push_to_destination"] = push_to_destination

        headers = {"Authorization": self.auth_header}

        response, _ = helix_request.post(url, json=payload, headers=headers)

        response_data = response.json() if response is not None else None
        status_code = response.status_code if response is not None else None
        return response_data, status_code

    def upload_file_to_sftp(self, local_path, remote_path, remove_existing_files=None):
        url = f"{self.config.url}{self.UPLOAD_ENDPOINT}"
        payload = {"directory": remote_path}
        if remove_existing_files:
            payload["remove_existing_files"] = str(remove_existing_files)
        files = [
            (
                "file",
                (
                    local_path,
                    open(local_path, "rb"),
                    "application/json",
                ),
            )
        ]
        headers = {"Authorization": self.auth_header}
        response, _ = helix_request.post(
            url, headers=headers, data=payload, files=files
        )

        response_data = response.json() if response is not None else None
        status_code = response.status_code if response is not None else None
        return response_data, status_code
