import pytz
from residents.managers.registered_device import ResidentRegisteredDeviceManager
from residents.managers.access_log import ResidentAccessLogManager
from datetime import datetime, timedelta
from django.db import connection
from log_request_id import local
from user_agents import parse
from common.constants import LOCKOUT_RELEASE_IN_MINS
from helixauth.managers.registered_device import RegisteredDeviceManager
from helixauth.managers.access_log import AccessLogManager


def update_device_access(user, refresh, device_detail={}, location_detail={}):
    if not device_detail:
        device_detail = {}
    if not user:
        return
    agent = getattr(local, "user_agent", None)
    ip = device_detail.get("ip_address")
    if not ip:
        ip = getattr(local, "ip_address", None)
    user_agent = parse(agent)
    device_fingerprint = device_detail.get("device_fingerprint")
    if not device_detail.get("make"):
        device_detail["make"] = user_agent.device.family
    if not device_detail.get("model"):
        device_detail["model"] = (
            user_agent.device.model if user_agent.device.model else "Other"
        )
    if not device_detail.get("os_detail"):
        device_detail["os_detail"] = "{} {}".format(
            user_agent.os.family, user_agent.os.version_string
        )
    if not device_detail.get("mac_address"):
        device_detail["mac_address"] = "N/A"
    device_detail["user"] = str(user.id)
    device_detail["last_ip_address"] = ip
    if device_fingerprint:
        device_detail["device_fingerprint"] = device_fingerprint

    registered_device_manager = RegisteredDeviceManager()
    registered_device = (
        registered_device_manager.check_device_detail_and_store_on_login(device_detail)
    )
    if registered_device:
        access_log_manager = AccessLogManager()
        access_log_manager.log_user_access_from_device(
            user, refresh, registered_device, ip, location_detail
        )


def update_resident_device_access(
    user, refresh, device_detail={}, location_detail={}, jti=None, exp=None
):
    if not device_detail:
        device_detail = {}
    if not user:
        return
    agent = getattr(local, "user_agent", None)
    ip = device_detail.get("ip_address")
    if not ip:
        ip = getattr(local, "ip_address", None)
    user_agent = parse(agent)
    device_fingerprint = device_detail.get("device_fingerprint")
    if not device_detail.get("make"):
        device_detail["make"] = user_agent.device.family
    if not device_detail.get("model"):
        device_detail["model"] = (
            user_agent.device.model if user_agent.device.model else "Other"
        )
    if not device_detail.get("os_detail"):
        device_detail["os_detail"] = "{} {}".format(
            user_agent.os.family, user_agent.os.version_string
        )
    if not device_detail.get("mac_address"):
        device_detail["mac_address"] = "N/A"
    device_detail["user"] = str(user.id)
    device_detail["last_ip_address"] = ip
    if device_fingerprint:
        device_detail["device_fingerprint"] = device_fingerprint

    registered_device_manager = ResidentRegisteredDeviceManager()
    registered_device = (
        registered_device_manager.check_device_detail_and_store_on_login(device_detail)
    )
    if registered_device:
        access_log_manager = ResidentAccessLogManager()
        access_log_manager.log_user_access_from_device(
            user, refresh, registered_device, ip, location_detail, jti, exp
        )


def is_within_lockout_duration(user):
    if not user:
        return True
    tenant = connection.tenant
    lockout_exp_duration = (
        tenant.lockout_release_duration if tenant else LOCKOUT_RELEASE_IN_MINS
    )
    if user.locked and datetime.now().replace(tzinfo=pytz.utc) < user.locked_at.replace(
        tzinfo=pytz.utc
    ) + timedelta(minutes=lockout_exp_duration):
        return True
    return False


def get_lockout_duration(user):
    tenant = connection.tenant
    lockout_exp_duration = (
        tenant.lockout_release_duration if tenant else LOCKOUT_RELEASE_IN_MINS
    )
    return user.locked_at.replace(tzinfo=pytz.utc) + timedelta(
        minutes=lockout_exp_duration
    )
