import csv

from common.utils.logging import logger
from payments.constants import CANCELLATION_CODE_COMPOSITIONS_FILE_PATH
from payments.models import BillCancellationCodeComposition


class BillCancellationCodeCompositionManager:
    @classmethod
    def seed_cancellation_code_composition(cls):
        logger.info("Loading bill cancellation code compositions...")
        bill_cancellation_code_compositions = list(
            csv.DictReader(open(CANCELLATION_CODE_COMPOSITIONS_FILE_PATH))
        )
        for code_composition in bill_cancellation_code_compositions:
            cancellation_code = code_composition["cancellation_code"]
            cancellation_reason = code_composition["cancellation_reason"]
            BillCancellationCodeComposition.objects.update_or_create(
                cancellation_code=cancellation_code,
                cancellation_reason=cancellation_reason,
            )

        logger.info("Loaded bill cancellation code compositions")
