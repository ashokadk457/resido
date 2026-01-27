import mimetypes
from io import BytesIO

import requests

from common.utils.logging import logger


def download_remote_file_as_email_attachment(file_urls):
    """Download file content and return as files objects as required by email service."""
    files = []
    try:
        # Download the file
        for file_url in file_urls:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Get the file name from the URL
            file_name = file_url.split("?")[0].split("/")[-1]
            file_content = BytesIO(response.content)  # Wrap content in a BytesIO object

            # Guess MIME type
            mimetype, _ = mimetypes.guess_type(file_name)
            if not mimetype:
                mimetype = "application/octet-stream"  # Default MIME type

            # Prepare the files payload
            files.append(
                (
                    "file",
                    (
                        file_name,
                        file_content,
                        mimetype,
                    ),
                )
            )
    except Exception as e:
        logger.error(f"Error Occured while fetching email attchment from asset. :- {e}")
        return False
    return files
