import string
import uuid
import os
import re
import random
from uuid import uuid4
from itertools import tee
from datetime import datetime
from django.db import transaction
import requests
from django.conf import settings
from django.db import connection
from django.utils.deconstruct import deconstructible
from django.db.models import Q
from geopy.distance import distance as geopy_distance
from rest_framework import status

from common.models import HealthCareCustomer
from common.errors import ERROR_DETAILS

optional = {"null": True, "blank": True}


def get_org_prefix():
    customer = HealthCareCustomer.objects.get(schema_name=connection.schema_name)
    name = customer.name.upper()
    name = name.split(" ")
    if len(name) > 1:
        return name[0][0] + name[1][0]
    else:
        return name[0][:2]


def get_display_id(model, prefix="REFIN"):
    name = get_org_prefix().upper()
    name += prefix
    display_id = model.display_id
    if model._state.adding:
        with transaction.atomic():
            last_id = (
                model.__class__.objects.all()
                .exclude(display_id__isnull=True)
                .exclude(display_id__exact="")
                .filter(display_id__startswith=name)
                .select_for_update()
                .order_by("-display_id")
                .values_list("display_id", flat=True)
                .first()
            )

            if last_id is not None:
                reg = re.compile(r"[a-zA-Z]+(?P<last_id>[0-9]+)$")
                obj = reg.search(last_id)
                if obj and obj.group(1):
                    next_num = int(obj.group(1)) + 1
                else:
                    next_num = 10000001
                display_id = str(name) + str(next_num)
            else:
                display_id = name + "10000001"
    return display_id


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        # get filename
        if instance.pk:
            filename = "{}.{}".format(instance.pk, ext)
        else:
            # set filename as random string
            filename = "{}.{}".format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)


def get_location_latlng(address):
    address_url = str(settings.ADDRESS_URL)
    location_search_url = (
        f"{address_url}/search?layers=venue,address&text={address}&boundary.country=USA"
    )
    location_search_response = requests.get(location_search_url)
    if location_search_response.status_code != status.HTTP_400_BAD_REQUEST:
        location_search_response.raise_for_status()
        location_results = location_search_response.json().get("features", [])
        if location_results:
            for location_found in location_results:
                latlng = location_found["geometry"]["coordinates"]
                return latlng
    else:
        return None


def get_title_string(field_value):
    field_data = str(field_value).title()
    return field_data


def validate_npi(npi):
    npi = str(npi)
    npi = npi.strip()
    token = "Token " + str(settings.SERVICES_KEY)
    url = str(settings.SERVICES_URL) + "/provider/?npi=" + str(npi)
    payload = {}
    headers = {"Authorization": token}
    response = requests.request("GET", url, headers=headers, data=payload)
    res = response.json()
    if "code" in res and res["code"] == 5001:
        return False
    else:
        return True


def is_resident_request(request):
    return hasattr(request, "is_resident") and getattr(request, "is_resident")


def round_minute(date: datetime = None, round_to: int = 1):
    """
    round datetime object to minutes
    """
    if not date:
        date = datetime.now()
    date = date.replace(second=0, microsecond=0)
    delta = date.minute % round_to
    return date.replace(minute=date.minute - delta)


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value), version=4)
        return True
    except ValueError:
        return False


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def get_latlng_distance(point1, point2):
    points = (point1, point2)
    d = sum(geopy_distance(a, b).meters for (a, b) in pairwise(points))
    distance_km = d / 1000
    distance_miles = distance_km * 0.621371
    return distance_miles


def is_helix_user_request(request):
    return (
        not request.user.is_anonymous
        and hasattr(request, "is_helix_user")
        and getattr(request, "is_helix_user")
    )


# Method to change the prefix of address attributes
def replace_address_attrs(data, from_prefix, to_prefix):
    attrs = (
        "address",
        "address_1",
        "city",
        "state",
        "zipcode",
        "country",
    )
    for attr in attrs:
        value = data.pop(from_prefix + attr, None)
        new_attr = to_prefix + attr
        # if value:
        data[new_attr] = value
    return data


def get_user_id(user, data):
    from common.exception import StandardAPIException

    if data.get("user_id"):
        user_id = data.get("user_id")
    else:
        user_id = user.id
    if not is_valid_uuid(user_id):
        raise StandardAPIException(
            code="invalid_data_type",
            detail=ERROR_DETAILS["invalid_data_type"].format(
                param="user_id", expected="User ID"
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return user_id


def validate_case_insensitive_unique(value, model_class, field_name, instance=None):
    from common.exception import StandardAPIException

    filter_kwargs = {f"{field_name}__iexact": value}
    qs = model_class.objects.filter(Q(**filter_kwargs))

    if instance and instance.id:
        qs = qs.exclude(id=instance.id)

    if qs.exists():
        raise StandardAPIException(
            code="name_already_exist",
            detail=ERROR_DETAILS["name_already_exist"].format(
                class_name=model_class.__name__, field_name=field_name
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def get_random_string(n):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(n))
