import os

from common.utils.enum import EnumWithValueConverter


class AuthenticateType(EnumWithValueConverter):
    refresh_token = "refresh_token"
    login_with_otp = "login_with_otp"
    login_with_password = "login_with_password"
    validate_otp = "validate_otp"
    validate_security_question = "validate_security_question"
    activate_and_authenticate = "activate_and_authenticate"


class AddressTypes(EnumWithValueConverter):
    home = "home"
    work = "work"


class NotificationChannel(EnumWithValueConverter):
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


class SystemPlatform(EnumWithValueConverter):
    WEBAPP = "WEBAPP"
    ANDROID = "ANDROID"
    IOS = "IOS"
    WINDOWS = "WINDOWS"


class UsernameType(EnumWithValueConverter):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    UUID = "UUID"


DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "+1")

RESET_PASSWORD_URL = "https://{domain}/#/reset-password?code={code}&user_id={user_id}&user_type={user_type}"
CREATE_PASSWORD_URL = "https://{domain}/#/create-password?code={code}&user_id={user_id}&user_type={user_type}"


class PolicyDocType(EnumWithValueConverter):
    t_and_c = "t_and_c"
    policy = "policy"


class AccessLevel(EnumWithValueConverter):
    Admin = "admin"
    Customer = "customer"
    Property = "property"
    Location = "location"
    Building = "building"
    Floor = "floor"
    Unit = "unit"
