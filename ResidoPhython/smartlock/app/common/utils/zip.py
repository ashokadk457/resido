import os
import py7zr
from zipfile import ZipFile
from common.utils.logging import logger
from django.utils.crypto import get_random_string


class ZipHandler:
    def __init__(self, file=None):
        self.file = file
        self.zip_file = ZipFile(file=self.file, mode="x") if file else None
        self.content_list = self.zip_file.infolist() if self.zip_file else None

    def extract_all_from_zip_file(self, destination_directory):
        logger.info("Extracting zip contents")
        self.zip_file.extractall(destination_directory)

    def zip(self, file_paths):
        # with ZipFile(zip_file_path, 'w') as zipfile:
        for file in file_paths:
            if os.path.isfile(file):
                self.zip_file.write(file, os.path.basename(file))
                logger.info(f"Added {file} to {self.file}")
            else:
                logger.info(f"File {file} not found, skipping.")

    @classmethod
    def _7zip(cls, zip_name, input_files, password=None):
        with py7zr.SevenZipFile(zip_name, mode="w", password=password) as archive:
            for file in input_files:
                filename_only = os.path.basename(file)
                archive.write(file, arcname=filename_only)

        return zip_name

    def seven_zip(self, zip_name, input_files, set_password=True):
        password = None if not set_password else get_random_string(7)
        return (
            self._7zip(zip_name=zip_name, input_files=input_files, password=password),
            password,
        )
