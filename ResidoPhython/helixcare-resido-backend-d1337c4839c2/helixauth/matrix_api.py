import hmac
import hashlib
import requests
import json


class MatrixAPI:
    URL = "https://matrix.helixbeat.com/"

    def _generate_mac(self, nonce, user, password, admin=False, user_type=None):
        mac = hmac.new(
            key=b"-od8TGkIbkWYnyX2+~saNUYe:7n@KV*mSFcxCtKO3TjJXl9_X8",
            digestmod=hashlib.sha1,
        )

        mac.update(nonce.encode("utf8"))
        mac.update(b"\x00")
        mac.update(user.encode("utf8"))
        mac.update(b"\x00")
        mac.update(password.encode("utf8"))
        mac.update(b"\x00")
        mac.update(b"admin" if admin else b"notadmin")
        if user_type:
            mac.update(b"\x00")
            mac.update(user_type.encode("utf8"))

        return mac.hexdigest()

    def _get_nonce(self):
        response = requests.request("GET", self.URL + str("_synapse/admin/v1/register"))
        response = response.json()
        return response["nonce"]

    def create_user(self, username, displayname, password):
        try:
            nonce = self._get_nonce()
            payload = {
                "nonce": nonce,
                "username": username,
                "displayname": displayname,
                "password": password,
                "admin": False,
                "mac": self._generate_mac(nonce, username, password),
            }
            headers = {
                "Authorization": "Bearer syt_cGVwcGVyX3Jvbmkx_ACPbilQYNojVLEAzLmCq_2oToO9",
                "Content-Type": "application/json",
            }

            response = requests.request(
                "POST",
                self.URL + str("_synapse/admin/v1/register"),
                headers=headers,
                data=json.dumps(payload),
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(response.status_code)
                return {}
        except Exception as e:
            print("Error!" + e)
            return {}
