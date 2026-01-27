from django.core.files.base import ContentFile

from assets.models import Asset
from common.utils.logging import logger


class AssetManager:
    def __init__(self, **kwargs):
        self.file_path = kwargs.get("file_path")
        self.file_name = kwargs.get("file_name")
        self.asset_type = kwargs.get("asset_type") or "doc"
        self.asset_obj = kwargs.get("asset_obj")

    def _get_content_file_obj(self):
        if not self.file_path:
            return

        with open(self.file_path, "rb") as f:
            file_bytes = f.read()
        return ContentFile(file_bytes, name=self.file_name)

    def upload(self):
        if not self.file_path or not self.file_name:
            logger.info("Cannot upload asset. File path or file name is empty.")
            return

        file_content_obj = self._get_content_file_obj()
        if not file_content_obj:
            logger.info("Cannot upload asset. file content obj is empty")
            return

        self.asset_obj = Asset.objects.create(
            file=file_content_obj, filename=self.file_name, type=self.asset_type
        )
        return self.asset_obj
