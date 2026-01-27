from payments.gateway.easypay.constants import (
    EASY_PAY_URL,
    EASY_PAY_ACC_CODE,
    EASY_PAY_ACC_TOKEN,
)


class EasyPayConfiguration:
    @classmethod
    def init(cls):
        # TODO put a null safe check to see if the configuration is present in the env var

        return cls()

    def __init__(self):
        self.base_url = EASY_PAY_URL
        self.acc_code = EASY_PAY_ACC_CODE
        self.token = EASY_PAY_ACC_TOKEN
