import re


class DictUtils:
    @classmethod
    def _convert_to_snakecase(cls, name):
        return re.sub(pattern=r"(?<!^)(?=[A-Z])", repl="_", string=name).lower()

    @classmethod
    def convert_camelcase_dict_to_snake_case_dict(cls, data):
        if isinstance(data, dict):
            return {
                cls._convert_to_snakecase(
                    name=key
                ): cls.convert_camelcase_dict_to_snake_case_dict(data=value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                cls.convert_camelcase_dict_to_snake_case_dict(data=item)
                for item in data
            ]

        return data
