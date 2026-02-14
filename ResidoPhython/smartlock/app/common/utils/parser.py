import json

from rest_framework.parsers import BaseParser


class WebhookJSONParser(BaseParser):
    media_type = "application/webhook+json"

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return json.load(stream)
        except json.JSONDecodeError as e:
            raise e
