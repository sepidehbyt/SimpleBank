from rest_framework import permissions
from identity.enums import RoleType


class IsRegularUser(permissions.BasePermission):
    message = 'only users are permitted.'

    def has_permission(self, request, view):
        if request.user.role == RoleType.USER.value:
            return True
        return False


class IsStaff(permissions.BasePermission):
    message = 'only staff are permitted.'

    def has_permission(self, request, view):
        if request.user.role == RoleType.BRANCH_MANAGER.value:
            return True
        return False
