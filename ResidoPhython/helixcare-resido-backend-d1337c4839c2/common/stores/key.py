import os

from common.constants import TEST_ENVIRONMENT, LOCAL_ENVIRONMENT
from common.stores.sample import SampleTestKeys
from resido.settings import TN_AUTH_PUBLIC_KEY, TN_AUTH_PRIVATE_KEY


class KeyStore:
    def __init__(self, environment):
        self.environment = environment

    @property
    def tn_auth_public_key(self):
        if self.environment == TEST_ENVIRONMENT:
            return SampleTestKeys.TN_AUTH_PUBLIC_KEY
        return TN_AUTH_PUBLIC_KEY

    @property
    def tn_auth_private_key(self):
        if self.environment == TEST_ENVIRONMENT:
            return SampleTestKeys.TN_AUTH_PRIVATE_KEY
        return TN_AUTH_PRIVATE_KEY


key_store = KeyStore(environment=os.getenv("ENVIRONMENT", LOCAL_ENVIRONMENT))
