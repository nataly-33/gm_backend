def log_action(user, action: str, resource_type: str = '', resource_id: str = '',
               details: dict = None, request=None) -> None:
    """
    Registra una acción en el audit log.
    Llamar desde services y tasks después de operaciones importantes.
    """
    from apps.audit.models import AuditLog

    ip = ''
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR', '')

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else '',
        ip_address=ip,
        details=details,
    )
