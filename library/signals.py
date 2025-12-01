from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.apps import apps


@receiver(post_migrate)
def create_groups_and_users(sender, **kwargs):
    # Only run for this app
    if sender.name != 'library':
        return

    # Create groups
    admin_group, _ = Group.objects.get_or_create(name='admin')
    user_group, _ = Group.objects.get_or_create(name='user')

    # Assign permissions to admin group for Book model
    try:
        Book = apps.get_model('library', 'Book')
        ct = ContentType.objects.get_for_model(Book)
        perms = Permission.objects.filter(content_type=ct, codename__in=['add_book', 'change_book', 'delete_book'])
        for p in perms:
            admin_group.permissions.add(p)
    except Exception:
        pass

    # Create default users if they don't exist
    try:
        # Admin user 'Moteeees'
        admin_user, created = User.objects.get_or_create(username='Moteeees')
        if created:
            admin_user.set_password('Moteeees123')
        # ensure staff so can access admin site
        admin_user.is_staff = True
        admin_user.save()
        admin_group.user_set.add(admin_user)

        # Regular user 'user'
        normal_user, created = User.objects.get_or_create(username='user')
        if created:
            normal_user.set_password('user1234')
            normal_user.save()
        user_group.user_set.add(normal_user)
    except Exception:
        pass
