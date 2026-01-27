import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

from common.utils.logging import logger
from common.utils.requests import helix_request
from external.hus.configuration import HUSConfiguration


class HelixUtilityService:
    PUSH_NOTIFICATION_ENDPOINT = "/push-notifications"

    @classmethod
    def init(cls, config: HUSConfiguration):
        return cls(config=config)

    def __init__(self, config=None):
        self.config = config or HUSConfiguration.init()
        self.token = f"Token {self.config.token}"
        self.headers = {"Authorization": self.token}

    def send_sms(self):
        pass

    def send_email(self):
        pass

    def send_push_notification(self, push_notif_payload):
        """

            [
                {
                    "device_token": "",
                    "title": "",
                    "body": "",
                    "data": {}
                }
            ]

        @param push_notif_payload: dict
        @return:
        """
        if not push_notif_payload:
            logger.info("No push notification payload")
            return None, None

        url = f"{self.config.url}{self.PUSH_NOTIFICATION_ENDPOINT}"
        response, _ = helix_request.post(
            url=url, headers=self.headers, json=push_notif_payload
        )
        if isinstance(response, dict) and not response.get("status"):
            return (response,)

        if response is None:
            return None, None

        return response.json(), response.status_code

    @staticmethod
    def get(endpoint, params=None):
        if params is None:
            params = {}

        token = "Token " + str(settings.SERVICES_KEY)
        url = f"{settings.SERVICES_URL}/{endpoint}"
        headers = {"Authorization": token}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            return Response(
                {"message": f"HTTP error occurred: {http_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.ConnectionError as conn_err:
            return Response(
                {"message": f"Connection error occurred: {conn_err}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.Timeout as timeout_err:
            return Response(
                {"message": f"Request timed out: {timeout_err}"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.RequestException as req_err:
            return Response(
                {"message": f"An error occurred: {req_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(response.json(), content_type="application/json")

    @staticmethod
    def post(endpoint, data=None):
        if data is None:
            data = {}

        token = "Token " + str(settings.SERVICES_KEY)
        url = f"{settings.SERVICES_URL}/{endpoint}"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP error responses
        except requests.HTTPError as http_err:
            return Response(
                {"message": f"HTTP error occurred: {http_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.ConnectionError as conn_err:
            return Response(
                {"message": f"Connection error occurred: {conn_err}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.Timeout as timeout_err:
            return Response(
                {"message": f"Request timed out: {timeout_err}"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.RequestException as req_err:
            return Response(
                {"message": f"An error occurred: {req_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(response.json(), content_type="application/json")

    @staticmethod
    def put(endpoint, data=None):
        if data is None:
            data = {}

        token = "Token " + str(settings.SERVICES_KEY)
        url = f"{settings.SERVICES_URL}/{endpoint}"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        try:
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP error responses
        except requests.HTTPError as http_err:
            return Response(
                {"message": f"HTTP error occurred: {http_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.ConnectionError as conn_err:
            return Response(
                {"message": f"Connection error occurred: {conn_err}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.Timeout as timeout_err:
            return Response(
                {"message": f"Request timed out: {timeout_err}"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.RequestException as req_err:
            return Response(
                {"message": f"An error occurred: {req_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(response.json(), content_type="application/json")
