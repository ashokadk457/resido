# from functools import lru_cache

from django import forms
from django.db import models, connection
from rest_framework.serializers import (
    ModelSerializer,
    ChoiceField,
    UUIDField,
    DateTimeField,
    CharField,
)
from common.serializer_mixin import AttributeLevelPermissionMixin
from common.utils.currency import get_currency_codes
from lookup.models import Lookup


# @lru_cache(maxsize=512)   # temporarily commented lru cache
def get_lookups(lookup_name, tenant):
    lookups = Lookup.objects.filter_from_cache(name=lookup_name)
    if not lookups:
        return []

    return [(lookup["code"], lookup["value"]) for lookup in lookups]


class LookupField(models.CharField):
    """A charfield which gets the choices from the DB
    Apart from regular CharField, it has a mandatory lookup_code
    """

    def __init__(self, lookup_name, *args, **kwargs):
        self.lookup_name = lookup_name
        self.required = lookup_name
        super(LookupField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(LookupField, self).deconstruct()
        # print("Values {} {} {}".format(name, args, kwargs))
        if self.lookup_name:
            kwargs["lookup_name"] = self.lookup_name
        return name, path, args, kwargs

    def get_choices(self, *args, **kwargs):
        get_lookups(lookup_name=self.lookup_name, tenant=connection.tenant)


class LookupFormField(forms.ChoiceField):
    def __init__(
        self,
        choices=(),
        required=True,
        allow_null=False,
        widget=None,
        label=None,
        initial=None,
        help_text="",
        *args,
        **kwargs
    ):
        if allow_null:
            self.required = False
        if "max_length" in kwargs:
            kwargs.pop("max_length")
        super(LookupFormField, self).__init__(
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            *args,
            **kwargs
        )
        if choices:
            self.choices = choices

    def valid_value(self, value):
        return True


class BaseSerializer(AttributeLevelPermissionMixin, ModelSerializer):
    id = UUIDField(read_only=True)
    display_id = CharField(read_only=True)
    created_on = DateTimeField(read_only=True)
    updated_on = DateTimeField(read_only=True)
    created_by = UUIDField(read_only=True)
    updated_by = UUIDField(read_only=True)

    "Subclasses ModelSerializer to add special handling for lookups"

    def __init__(self, *args, **kwargs):
        super(BaseSerializer, self).__init__(*args, **kwargs)
        if kwargs.get("context") and kwargs.get("context").get("pop_fields"):
            pop_them = kwargs.get("context").get("pop_fields")
            for other in pop_them:
                self.fields.pop(other)

    def build_standard_field(self, field_name, model_field):
        if isinstance(model_field, LookupField):
            return (
                LookupSerializerField,
                {
                    "lookup_name": model_field.lookup_name,
                    "required": False,
                    "allow_null": True,
                },
            )
        return super(BaseSerializer, self).build_standard_field(field_name, model_field)

    def to_representation(self, instance):
        """Convert currency codes to symbols for all currency fields"""
        resp = super().to_representation(instance)

        # Convert all currency fields (fields ending with _currency) to symbols
        if isinstance(resp, dict):
            for field_name, field_value in resp.items():
                if field_name.endswith("_currency") and field_value:
                    try:
                        currency_symbol = get_currency_codes(field_value)
                        if currency_symbol:
                            resp[field_name] = currency_symbol
                    except Exception:
                        # If conversion fails, keep the original value
                        pass

        return resp


LookupModelSerializer = BaseSerializer


class LookupSerializerField(ChoiceField):
    def __init__(self, *args, **kwargs):
        self.lookup_name = kwargs.get("lookup_name")
        kwargs.pop("lookup_name", None)
        kwargs.pop("max_length", None)
        kwargs["choices"] = self.get_choices()
        super(LookupSerializerField, self).__init__(*args, **kwargs)

    def get_choices(self, *args, **kwargs):
        return get_lookups(lookup_name=self.lookup_name, tenant=connection.tenant)

    def to_representation(self, value):
        if self.parent.__class__.__name__ == "SlotSerializer":
            return self.choices.get(value, value)
        return super(LookupSerializerField, self).to_representation(value)


ModelSerializer.serializer_field_mapping[LookupField] = LookupSerializerField
