import requests
from django.conf import settings

from common.utils.requests import helix_request


class Helixxchange:
    PATIENT_PIPELINE = str(settings.XCHANGE_PATIENT_PIPELINE)
    JSON_TO_CCDA_API_ENDPOINT = "api/v1/parser/json_to_ccda"
    CCDA_TO_HTML_API_ENDPOINT = "api/v1/ccda-to-html"

    def __init__(self):
        self.token = None
        self.token = self.get_xchange_token()

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @classmethod
    def parse_response(cls, response, call_log):
        response_log = call_log.get("Response", {})
        if response_log.get("response_type") == "FAILURE":
            if response_log.get("exception"):
                return response_log.get("exception")
            return response_log.get("response_body")

        response_body = response.json()
        return response_body.get("data")

    def get_json_to_ccda(self, ccda_template_name, data_to_convert, mapping):
        url = f"{settings.XCHANGE_URL}/{self.JSON_TO_CCDA_API_ENDPOINT}"

        payload = {
            "template": ccda_template_name,
            "input_data": data_to_convert,
            "mapping_list": mapping,
        }
        response, call_log = helix_request.post(
            url=url,
            headers=self.headers,
            json=payload,
        )

        return self.parse_response(response=response, call_log=call_log)

    def get_ccda_to_html(self, patient_chart):
        url = f"{settings.XCHANGE_URL}/{self.CCDA_TO_HTML_API_ENDPOINT}"
        payload = {"ccda_xml": patient_chart}
        response, call_log = helix_request.post(
            url=url,
            headers=self.headers,
            json=payload,
        )
        return self.parse_response(response=response, call_log=call_log)

    def convert_patient_to_fhir(self, payload):
        token = self.get_xchange_token()
        if not token:
            print("Error in generating XChange token")
            return "Error in generating token"

        try:
            url = (
                f"{settings.XCHANGE_URL}/api/v1/customers/"
                f"{settings.XCHANGE_CUSTOMER}/pipelines/"
                f"{self.PATIENT_PIPELINE}/run"
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            print(response_json)
            if response_json["data"]["status"] == "Completed":
                return response_json["data"]["execution_run_output"]
            else:
                print(f"Exception in converting JSON to FHIR: {response_json['data']}")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error in callXChange: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error in callXChange: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error in callXChange: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error in callXChange: {req_err}")
        except KeyError as key_err:
            print(f"Key error in callXChange: {key_err}")
        return "Exception in converting the JSON to FHIR"

    def get_xchange_token(self):
        if self.token:
            return self.token

        try:
            url = f"{settings.XCHANGE_URL}/api/v1/token"
            payload = {
                "api_key": str(settings.XCHANGE_KEY),
                "api_secret": str(settings.XCHANGE_SECRET),
            }
            if settings.XCHANGE_EMAIL:
                url = f"{settings.XCHANGE_URL}/api/v1/user/login"
                payload = {
                    "email": settings.XCHANGE_EMAIL,
                    "password": settings.XCHANGE_PASSWORD,
                }
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            return response_json["data"]["access"]
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error in get_xchange_token: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error in get_xchange_token: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error in get_xchange_token: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error in get_xchange_token: {req_err}")
        except KeyError as key_err:
            print(f"Key error in get_xchange_token: {key_err}")
        return None
