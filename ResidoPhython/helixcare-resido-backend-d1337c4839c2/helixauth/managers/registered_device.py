from common.managers.model.base import BaseModelManager
from helixauth.models import RegisteredDevice


class RegisteredDeviceManager(BaseModelManager):
    model = RegisteredDevice

    def check_device_detail_and_store_on_login(self, device_detail):
        from helixauth.serializers import RegisteredDeviceSerializer

        device_detail_serializer = RegisteredDeviceSerializer(data=device_detail)
        device_detail_serializer.is_valid(raise_exception=True)
        device_detail_object = device_detail_serializer.save()
        if not device_detail_object.active:
            device_detail_object.active = True
            device_detail_object.os_detail = device_detail.get("os_detail")
            device_detail_object.save()
        return device_detail_object

    def update_last_ip_and_location_on_device(
        self, device_detail_object, ip, location_detail
    ):
        device_detail_object.last_ip_address = ip
        device_detail_object.last_location = location_detail
        device_detail_object.save()

    def get_all_active_registered_devices_of_user(self, user):
        return self.filter_by(user=user, active=True).order_by("-updated_on")

    def deactivate_device(self, device):
        device.active = False
        device.save()

    def get_active_device_token_and_platform(self, user):
        active_devices = self.get_all_active_registered_devices_of_user(user=user)
        if active_devices:
            _obj = active_devices.first()
            return _obj.device_token, _obj.platform

        return None, None
