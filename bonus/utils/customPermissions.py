from rest_framework import permissions


class IsRegularUser(permissions.BasePermission):
    message = 'only users ar permitted.'

    def has_permission(self, request, view):
        if not request.user.is_superuser:
            return True
        return False
