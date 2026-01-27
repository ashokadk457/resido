from notifications.models import NotificationQueue, NotificationSetting
import requests

from residents.models import Resident
from staff.models import HelixStaff


class Utils:
    def validate_number(self, number):
        try:
            URL = (
                "https://numlookupapi.com/api/validate/"
                + str(number)
                + "?apikey=109de230-1252-11ec-a432-bbff045daedf"
            )
            r = requests.get(url=URL)
            data = r.json()
            return data["valid"]
        except Exception:
            return False

    def update_queue(self, entry, status, notes):
        qEntry = NotificationQueue.objects.get(pk=entry.id)
        qEntry.status = status
        qEntry.notes = notes
        qEntry.save()

    def get_tenant_notification(type, event, lang):
        setting = (
            NotificationSetting.objects.filter(event_type=event)
            .filter(notification_type=type)
            .filter(language=lang)
        )
        return setting.first()

    def check_notification_type(patient):
        mode = "EMAIL"
        lang = "EN"
        pat = Resident.objects.filter(id=patient.id)
        pat = pat[0]
        if len(pat.communication_mode) != 0:
            mode = pat.communication_mode[0]
        if len(pat.user.languages_known) != 0:
            lang = pat.user.languages_known[0]
        return mode, lang

    def check_notification_type_provider(provider):
        mode = "EMAIL"
        lang = "EN"
        pro = HelixStaff.objects.filter(id=provider.id)
        pro = pro[0]
        if len(pro.communication_mode) != 0:
            mode = pro.communication_mode[0]
        if len(pro.user.languages_known) != 0:
            lang = pro.user.languages_known[0]
        return mode, lang


def get_resident_communication_details(id):
    query = Resident.objects.filter(id=id).first()
    if query is None:
        return None, None, None
    return query.user.email, query.user.phone, query.user.country_code


def get_staff_communication_details(id):
    query = HelixStaff.objects.filter(id=id).first()
    if query is None:
        return None, None, None
    return query.user.email, query.user.phone, query.user.country_code
