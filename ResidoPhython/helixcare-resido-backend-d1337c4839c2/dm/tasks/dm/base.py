import traceback

from django.db import transaction, connection

from common.utils.logging import logger


class BaseDataMigrationTask:
    def __init__(self, **kwargs):
        self.version = None

    def _run(self):
        raise NotImplementedError

    def run(self, **kwargs):
        if self.version is None:
            raise Exception(
                "Version not defined. Skipping running the data migration task."
            )

        # Check if we're already inside an atomic block
        prior_atomic = connection.in_atomic_block

        # Only manage transactions manually if not already in an atomic block
        if not prior_atomic:
            transaction.set_autocommit(False)

        try:
            self._run()
        except Exception as e:
            logger.info(
                f"Exception occurred while running the Data Migration task - {str(e)}"
            )
            traceback.print_exc()

            # Only rollback/restore autocommit if we started transaction management
            if not prior_atomic:
                transaction.rollback()
                transaction.set_autocommit(True)

            return False, str(e)
        else:
            # Only commit/restore autocommit if we started transaction management
            if not prior_atomic:
                transaction.commit()
                transaction.set_autocommit(True)

        return True, None
