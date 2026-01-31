from rest_framework.permissions import BasePermission

class HasBearerToken(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth) 
