import logging
from rest_framework import permissions

log = logging.getLogger(__name__)

PUBLIC = 'public'
ALL_AUTHENTICATED_USERS = 'all_authenticated_users'


class IsVisibleTo(permissions.BasePermission):

    def has_permission(self, request, view):
        # visible_to only applies to the introspect endpoint, return true otherwise
        if view.action_map.get(request.method.lower()) != 'introspect':
            return True

        if PUBLIC in view.visible_to:
            return True
        log.critical('View not marked as public, and fine-grained permissions have not been implemented!')
        return False


class IsRunnableBy(permissions.BasePermission):

    def has_permission(self, request, view):
        # runnable_by applies to everything except the introspect endpoint
        if view.action_map.get(request.method.lower()) == 'introspect':
            return True

        if ALL_AUTHENTICATED_USERS in view.runnable_by:
            return request.user.is_authenticated

        log.critical('View not marked as public, and fine-grained permissions have not been implemented!')
        return False