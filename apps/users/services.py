def create_user(email: str, password: str, full_name: str):
    from apps.users.models import User
    user = User.objects.create_user(email=email, password=password, full_name=full_name)
    assign_default_role(user)
    return user


def assign_default_role(user):
    from apps.users.models import Role, UserRole
    role, _ = Role.objects.get_or_create(name='user', defaults={'is_system': True})
    UserRole.objects.get_or_create(user=user, role=role)
