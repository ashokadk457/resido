from django.db.models import CharField
from django.core.validators import RegexValidator


class SafeCharField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs["validators"] = kwargs.get(
            "validators", [RegexValidator("[+/%*^!@#$]", inverse_match=True)]
        )
        super().__init__(*args, **kwargs)
