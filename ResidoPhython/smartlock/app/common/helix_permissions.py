from django.contrib.auth.models import Permission


def isSuperUser(user):
    return user.is_superuser


def isActive(user):
    return user.is_active


def checkPermission(user, roles):
    if isActive(user) is False:
        return False
    if isSuperUser(user):
        return True
    return user.has_perms(roles)


def _checkUserInGroup(user, group):
    if isActive(user) is False:
        return False
    return user.groups.filter(name=group).exists()


def isAdministrator(user):
    return _checkUserInGroup(user, "Administrator")


def isFacilityOps(user):
    return _checkUserInGroup(user, "Facility Ops")


def isProvider(user):
    return _checkUserInGroup(user, "Provider")


def isCareCoordinator(user):
    return _checkUserInGroup(user, "Care Coordinator")


def providerSelfRecordAccess(user, id):
    from staff.models import HelixStaff

    return HelixStaff.objects.filter(user=user, id=id).exists()


def get_user_permissions(user):
    if user.is_superuser:
        return Permission.objects.all()
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)


def get_user_group(user):
    return user.groups.all()
