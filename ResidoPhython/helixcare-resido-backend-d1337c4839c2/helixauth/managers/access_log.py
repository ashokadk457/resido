import datetime


from common.managers.access_log.base import BaseAccessLogManager
from common.managers.model.base import BaseModelManager
from helixauth.models import AccessLog
from helixauth.managers.registered_device import RegisteredDeviceManager


class AccessLogManager(BaseModelManager, BaseAccessLogManager):
    model = AccessLog

    @staticmethod
    def get_ip_from_request_meta(request_meta):
        x_forwarded_for = request_meta.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request_meta.get("REMOTE_ADDR")
        return ip

    def log_user_access_from_device(
        self, user, refresh_token, registered_device, ip, location_detail
    ):
        jti, exp_obj = self.get_details_from_refresh_token(refresh_token=refresh_token)
        self.create_object(
            user=user,
            device=registered_device,
            refresh_jti=jti,
            refresh_exp=exp_obj,
            refresh_token=refresh_token,
            ip_address=ip,
            location=location_detail,
            login_status="success" if refresh_token else "failure",
        )
        # TODO: put task in celery to lookup for location based on ip_address or lat/lng.
        # And call below function from that celery task
        RegisteredDeviceManager().update_last_ip_and_location_on_device(
            registered_device, ip, location_detail
        )

    def update_access_log_with_token(self, token, request_meta, location_detail=None):
        jti, _ = self.get_details_from_refresh_token(refresh_token=token)
        record = self.filter_by(refresh_jti=jti).first()
        if record:
            ip = self.get_ip_from_request_meta(request_meta)
            record.ip_address = ip
            record.location = location_detail
            record.save()
            # TODO: put task in celery to lookup for location based on ip_address or lat/lng
            # And call below function from that celery task
            RegisteredDeviceManager().update_last_ip_and_location_on_device(
                record.device, ip, location_detail
            )

    def get_all_active_tokens_for_device(self, user_id, device):
        current_time = datetime.datetime.now()
        return self.filter_by(
            user_id=user_id, device=device, refresh_exp__gt=current_time
        ).values_list("refresh_token", "refresh_jti")
