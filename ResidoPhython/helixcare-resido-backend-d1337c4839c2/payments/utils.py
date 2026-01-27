from datetime import datetime
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from rest_framework import status
from django.db.models import Q
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException


def decrypt_data_using_pvt_key(bytes_data, pvt_key):
    pr_key = RSA.import_key(pvt_key)
    decrypt = PKCS1_OAEP.new(key=pr_key)
    return decrypt.decrypt(bytes_data).decode("utf-8")


def filter_by_date_range(queryset, valid_from_date=None, valid_to_date=None):
    valid_from_date, valid_to_date = None, None
    if valid_from_date:
        try:
            valid_from_date = datetime.strptime(valid_from_date, "%Y-%m-%d")
        except ValueError:
            raise StandardAPIException(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="valid_for"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    if valid_to_date:
        try:
            valid_to_date = datetime.strptime(valid_to_date, "%Y-%m-%d")
        except ValueError:
            raise StandardAPIException(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="valid_for"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    if valid_from_date and valid_to_date:
        queryset = queryset.filter(
            Q(start_date__range=(valid_from_date, valid_to_date))
            | Q(start_date__isnull=True),
            Q(end_date__range=(valid_from_date, valid_to_date))
            | Q(end_date__isnull=True),
        )
    elif valid_from_date or valid_to_date:
        valid_date = valid_from_date or valid_to_date
        queryset = queryset.filter(
            Q(start_date__gte=valid_date)
            | Q(start_date__isnull=True)
            | Q(end_date__lte=valid_date)
            | Q(end_date__isnull=True),
        )
    return queryset


def filter_by_id(queryset, id):
    ids = id.split(",")
    queryset = queryset.filter(id__in=ids)
    return queryset
