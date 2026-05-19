from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """El usuario tiene rol 'admin' o es staff de Django."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_roles.filter(
            role__name='admin'
        ).exists()


class IsOwnerOrAdmin(BasePermission):
    """El objeto pertenece al usuario autenticado, o es admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user_id == request.user.id
