_DEFAULTS = {
    'song_ready':   ('Tu canción está lista',   'Ya puedes escucharla en tu biblioteca.'),
    'stem_ready':   ('Pistas separadas listas', 'Descarga los stems desde la sección de separación.'),
    'mix_ready':    ('Mix exportado',           'Tu mezcla está lista para descargar.'),
    'credit_grant': ('Créditos agregados',      'Se agregaron créditos a tu cuenta.'),
    'system':       ('Notificación',            ''),
}


def notify_user(user, type: str, reference_id: str = None, title: str = None, message: str = None) -> None:
    """Crea una notificación para el usuario. Llamado desde tasks.py de stems, mix y songs."""
    from apps.notifications.models import Notification

    default_title, default_msg = _DEFAULTS.get(type, ('Notificación', ''))
    Notification.objects.create(
        user=user,
        type=type,
        title=title or default_title,
        message=message or default_msg,
        reference_id=reference_id or '',
    )
