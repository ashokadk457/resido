from rest_framework import generics
from common.permissions import HelixUserBasePermission
from common.utils.logging import logger
from notifications.models import (
    NotificationDLFile,
    NotificationQueue,
    NotificationDL,
    NotificationUserDL,
    NotificationTemplate,
    NotificationMessage,
)
from notifications.serializers import (
    NotificationDLFileSerializer,
    NotificationQueueSerializer,
    NotificationDLSerializer,
    NotificationUserDLSerializer,
    NotificationTemplateSerializer,
    NotificationMessageSerializer,
)
from notifications.utils import (
    get_staff_communication_details,
    get_resident_communication_details,
)
from residents.models import Resident
from staff.models import HelixStaff
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
import requests
import json
import re
from common.helix_pagination import LargeResultsSetPagination


class PatientPushNotifications(generics.ListCreateAPIView):
    serializer_class = NotificationQueueSerializer
    permission_classes = [
        HelixUserBasePermission,
    ]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationQueue"

    def get_queryset(self):
        queryset = (
            NotificationQueue.objects.filter(user=self.kwargs.get("pk"))
            .filter(notification_setting__notification_type="PUSH")
            .filter(status=3)
        )
        return queryset


class NotificationDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = NotificationQueueSerializer
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationQueue"

    def get_queryset(self):
        return NotificationQueue.objects.all()


class NotificationDLList(generics.ListCreateAPIView):
    serializer_class = NotificationDLSerializer
    permission_classes = [
        HelixUserBasePermission,
    ]
    pagination_class = LargeResultsSetPagination
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationDL"

    def get_queryset(self):
        queryset = NotificationDL.objects.all()
        return queryset


class NotificationDLFileList(generics.ListCreateAPIView):
    serializer_class = NotificationDLFileSerializer
    permission_classes = [
        HelixUserBasePermission,
    ]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationDLFile"

    def get_queryset(self):
        queryset = NotificationDLFile.objects.all()
        return queryset


class NotificationDLFileDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = NotificationDLFileSerializer
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationDLFile"

    def get_queryset(self):
        return NotificationDLFile.objects.all()


class NotificationDLDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = NotificationDLSerializer
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationDLFile"

    def get_queryset(self):
        return NotificationDL.objects.all()


class NotificationUserDLList(generics.ListCreateAPIView):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("id", "dl")
    filter_fields = ("id", "dl")
    serializer_class = NotificationUserDLSerializer
    permission_classes = [
        HelixUserBasePermission,
    ]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationUserDL"

    def get_queryset(self):
        queryset = NotificationUserDL.objects.all()
        return queryset


class NotificationUserDLDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = NotificationUserDLSerializer
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationUserDL"

    def get_queryset(self):
        return NotificationUserDL.objects.all()


class NotificationTemplateList(generics.ListCreateAPIView):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [
        HelixUserBasePermission,
    ]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationTemplate"

    def get_queryset(self):
        queryset = NotificationTemplate.objects.all()
        return queryset


class NotificationTemplateDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = NotificationTemplateSerializer
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationTemplate"

    def get_queryset(self):
        return NotificationTemplate.objects.all()


class NotificationMessageAutomatedList(generics.ListCreateAPIView):
    serializer_class = NotificationMessageSerializer
    permission_classes = [
        HelixUserBasePermission,
    ]
    pagination_class = LargeResultsSetPagination
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationMessage"

    def get_queryset(self):
        queryset = NotificationMessage.objects.all()
        return queryset


class NotificationMessageList(APIView):
    def get(self, request):
        type = request.query_params.get("type", None)
        page = request.query_params.get("page", 1)
        type = int(type)
        query = ""
        to = request.query_params.get("to", None)
        if to is None or type is None:
            return Response(
                {"message": "Mandatory field missing", "code": 5001}, status=400
            )
        email, phone, country_code = get_resident_communication_details(to)
        if email is None and phone is None:
            email, phone, country_code = get_staff_communication_details(to)
        if email is None and phone is None:
            return Response({"message": "User is missing", "code": 5001}, status=400)
        if type == 1:
            query += "identifier=" + str(phone) + "&type=1"
        elif type == 2:
            query += "identifier=" + str(email) + "&type=2"
        if page is not None:
            query += "&page=" + str(page)
        token = "Token " + str(settings.SERVICES_KEY)
        url = str(settings.SERVICES_URL) + "/notification_list/?" + query
        payload = {}
        headers = {"Authorization": token}
        response = requests.request("GET", url, headers=headers, data=payload)
        res = response.json()
        if "previous" in res:
            res["previous"] = ""
        if "next" in res:
            next = res["next"]
            if next is not None:
                next = request.build_absolute_uri()
                i = 0
                try:
                    i = next.index("page=")
                except Exception:
                    i = 0
                if i != 0:
                    p = int(next[i + 5 : i + 6])
                    next = next.replace("page=" + str(p), "page=" + str(p + 1))
                else:
                    next = next + "&page=2"
                res["next"] = next
        return Response(res, content_type="application/json")


class NotificationSummaryList(APIView):
    def get(self, request):
        type = request.query_params.get("type", None)
        sender_id = getProvider(request.user)
        type = int(type)
        type1 = None
        type2 = None
        first_name_1 = None
        last_name_1 = None
        first_name_2 = None
        last_name_2 = None
        query = ""
        if type is None:
            return Response(
                {"message": "Mandatory field missing", "code": 5001}, status=400
            )
        # email, phone = getPatient(to)
        # if email is None and phone is None:
        #     email, phone = getProviderByID(to)
        # if email is None and phone is None:
        #     return Response({'message': "User is missing", 'code': 5001}, status=400)
        if type == 1:
            query += "type=1"
        elif type == 2:
            query += "type=2"

        token = "Token " + str(settings.SERVICES_KEY)
        url = str(settings.SERVICES_URL) + "/notification_summary_list/?" + query
        payload = {}
        headers = {"Authorization": token}
        response = requests.request("GET", url, headers=headers, data=payload)
        res = response.json()
        print(res)
        for x in res:
            if (
                res[x]["sender_identifier"] != ""
                and res[x]["sender_identifier"] is not None
            ):
                check1, type1, first_name_1, last_name_1 = getUserByPatientOrProvider(
                    res[x]["sender_identifier"]
                )
            if res[x]["rec_identifier"] != "" and res[x]["rec_identifier"] is not None:
                check2, type2, first_name_2, last_name_2 = getUserByPatientOrProvider(
                    res[x]["rec_identifier"]
                )
            print(type1)
            if type1 is not None and type1 == "patient":
                res[x]["first_name"] = first_name_1
                res[x]["last_name"] = last_name_1
                res[x]["key_id"] = res[x]["sender_identifier"]
            elif type2 is not None and type2 == "patient":
                res[x]["first_name"] = first_name_2
                res[x]["last_name"] = last_name_2
                res[x]["key_id"] = res[x]["rec_identifier"]
            elif type1 is not None or type2 is not None:
                if res[x]["sender_identifier"] == sender_id:
                    res[x]["first_name"] = first_name_2
                    res[x]["last_name"] = last_name_2
                    res[x]["key_id"] = res[x]["rec_identifier"]
                elif res[x]["rec_identifier"] == sender_id:
                    res[x]["first_name"] = first_name_1
                    res[x]["last_name"] = last_name_1
                    res[x]["key_id"] = res[x]["sender_identifier"]
            elif type1 is None and type2 is None:
                if type == 1:
                    match, count, who = getPatientOrProviderByMobile(res[x]["to"])
                    if who == "patient":
                        res[x]["first_name"] = match.first_name
                        res[x]["last_name"] = match.last_name
                        res[x]["key_id"] = match.id
                    else:
                        match, count, who = getPatientOrProviderByMobile(
                            res[x]["sender"]
                        )
                        if who == "patient":
                            res[x]["first_name"] = match.first_name
                            res[x]["last_name"] = match.last_name
                            res[x]["key_id"] = match.id
                        else:
                            match, count, who = getPatientOrProviderByMobile(
                                res[x]["to"]
                            )
                            res[x]["first_name"] = match.first_name
                            res[x]["last_name"] = match.last_name
                            res[x]["key_id"] = match.id
                else:
                    match, count, who = getPatientOrProviderByEmail(res[x]["to"])
                    if who == "patient":
                        res[x]["first_name"] = match.first_name
                        res[x]["last_name"] = match.last_name
                        res[x]["key_id"] = match.id
                    else:
                        match, count, who = getPatientOrProviderByEmail(
                            res[x]["sender"]
                        )
                        if who == "patient":
                            res[x]["first_name"] = match.first_name
                            res[x]["last_name"] = match.last_name
                            res[x]["key_id"] = match.id
                        else:
                            match, count, who = getPatientOrProviderByEmail(
                                res[x]["to"]
                            )
                            res[x]["first_name"] = match.first_name
                            res[x]["last_name"] = match.last_name
                            res[x]["key_id"] = match.id
        return Response(res, content_type="application/json")


class SendNotificationMessge(APIView):
    def post(self, request, pk):
        req = request.data
        if "type" not in req or pk is None:
            return Response(
                {"error": "Required parameters is missing or invalid."}, status=400
            )
        typ = int(req["type"])
        email, mobile, country_code = get_resident_communication_details(pk)
        if email is None and mobile is None:
            email, mobile, country_code = get_staff_communication_details(pk)
        if email is None and mobile is None:
            return Response({"message": "User is missing", "code": 5001}, status=400)
        sender_id = getProvider(request.user)
        if sender_id is None:
            return Response(
                {"error": "Required parameters is missing or invalid."}, status=400
            )
        if typ == 2:
            if "subject" not in req or "body" not in req:
                return Response(
                    {"error": "Required parameters is missing or invalid."}, status=400
                )
            ret = sendEmail(req["subject"], req["body"], [email], sender_id, pk)
        if typ == 1:
            if "body" not in req:
                return Response(
                    {"error": "Required parameters is missing or invalid."}, status=400
                )
            ret = sendSMS(
                to=mobile,
                message=req["body"],
                sender_id=sender_id,
                rec_id=pk,
                country_code=country_code,
            )
            ret.pop("status_code", None)
        return Response(ret, content_type="application/json")


def sendEmail(
    subject,
    message,
    emails,
    sender_id,
    rec_id,
    files=None,
    sender_name=None,
    cc=None,
    bcc=None,
    html_message=None,
):
    # TODO move this to HelixUtilityService class
    """

    @param subject:
    @param message:
    @param emails: list of strings representing the email addresses to send the email to
    @param sender_id:
    @param rec_id:
    @param files:
    @param sender_name: string representing the custom name to appear as the sender when the receiver opens the email
    @param cc: list of strings representing the CC emails
    @param bcc: list of strings representing the BCC emails
    @param html_message: HTML content to send as email body
    @return:
    """
    ret = {}
    url = str(settings.SERVICES_URL) + "/send_email/"
    payload = {
        "subject": subject,
        "message": message,
        "emails": emails,  # Represents the "to" parameter
        "sender_id": sender_id,
        "rec_id": rec_id,
    }
    if html_message:
        payload["html_message"] = html_message
    content_type = "application/json" if files is None else None
    token = "Token " + str(settings.SERVICES_KEY)
    headers = {"Authorization": token}
    if content_type:
        headers["Content-Type"] = content_type
    kwargs = {
        "method": "POST",
        "url": url,
        "headers": headers,
    }
    if cc:
        payload["cc"] = cc if isinstance(cc, list) else [cc]
    if bcc:
        payload["bcc"] = bcc if isinstance(bcc, list) else [bcc]
    if sender_name:
        payload["sender_name"] = sender_name

    if files:
        kwargs["files"] = files
        kwargs["data"] = payload
    else:
        kwargs["data"] = json.dumps(payload)
    if cc:
        payload["cc"] = cc if isinstance(cc, list) else [cc]
    if bcc:
        payload["bcc"] = bcc if isinstance(bcc, list) else [bcc]
    if sender_name:
        payload["sender_name"] = sender_name
    try:
        response = requests.request(**kwargs)
        res = response.json()
        logger.info(f"Response from sendEmail API: {res}")
        ret["message"] = res
    except requests.exceptions.HTTPError as errh:
        print(errh)
        ret["message"] = errh
    except requests.exceptions.ConnectionError as errc:
        print(errc)
        ret["message"] = errc
    except requests.exceptions.Timeout as errt:
        print(errt)
        ret["message"] = errt
    except requests.exceptions.RequestException as err:
        print(err)
        ret["message"] = err
    else:
        ret["status_code"] = response.status_code
    return ret


def sendSMS(to, message, sender_id, rec_id, country_code=None):
    # TODO Move the core send sms logic to HelixUtilityService class
    ret = {"message": None, "status_code": 400}
    url = str(settings.SERVICES_URL) + "/send_sms/"
    if to and not to.startswith("+") and country_code:
        to = f"{country_code}{to}"
    payload = json.dumps(
        {"to_number": to, "body": message, "sender_id": sender_id, "rec_id": rec_id}
    )
    token = "Token " + str(settings.SERVICES_KEY)
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        res = response.json()
        ret["message"] = res
        ret["status_code"] = response.status_code
        logger.info(f"Response from sendSMS API: {res}")
        return ret
    except requests.exceptions.HTTPError as errh:
        print(errh)
        ret["message"] = errh
    except requests.exceptions.ConnectionError as errc:
        print(errc)
        ret["message"] = errc
    except requests.exceptions.Timeout as errt:
        print(errt)
        ret["message"] = errt
    except requests.exceptions.RequestException as err:
        print(err)
        ret["message"] = err

    ret["status_code"] = None
    return ret


def getProvider(user):
    query = HelixStaff.objects.filter(user=user).first()
    if query is None:
        return None
    return str(query.id)


class NotificationMessageDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = NotificationMessageSerializer
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "NotificationMessage"

    def get_queryset(self):
        return NotificationMessage.objects.all()


def getUserByPatientOrProvider(id):
    match = None
    who = ""
    try:
        match = HelixStaff.objects.get(id=id)
        who = "provider"
    except HelixStaff.DoesNotExist:
        pass
    if match is None:
        try:
            match = Resident.objects.get(id=id)
            who = "patient"
        except Resident.DoesNotExist:
            pass
    if match is not None:
        return match.user.id, who, match.user.first_name, match.user.last_name
    return None


def getPatientOrProviderByMobile(mobile):
    match = None
    count = 0
    who = None
    mobile = re.sub("[^A-Za-z0-9]+", "", mobile)
    try:
        match = (
            HelixStaff.objects.filter(user__phone__icontains=mobile)
            .filter(user__is_active=1)
            .first()
        )
        who = "provider"
    except HelixStaff.DoesNotExist:
        pass
    if match is None:
        try:
            match = (
                Resident.objects.filter(phone_number__icontains=mobile)
                .filter(user__is_active=1)
                .first()
            )
            who = "patient"
        except Resident.DoesNotExist:
            pass
    return match, count, who


def getPatientOrProviderByEmail(email):
    match = None
    count = 0
    who = None
    try:
        match = (
            HelixStaff.objects.filter(user__email__iexact=email)
            .filter(user__is_active=1)
            .first()
        )
        who = "provider"
    except HelixStaff.DoesNotExist:
        pass
    if match is None:
        try:
            match = (
                Resident.objects.filter(user__email__iexact=email)
                .filter(user__is_active=1)
                .first()
            )
            who = "patient"
        except Resident.DoesNotExist:
            pass
    return match, count, who
