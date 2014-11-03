from django.conf import settings

from .utils import get_function_for

ACF  = 'ROSETTA_ACCESS_CONTROL_FUNCTION'
AUTH = 'ROSETTA_REQUIRES_AUTH'

def can_translate(user):
    """Return a True if a user can access the Rosetta views"""
    return get_function_for(ACF, default_control_test)(user)

# Default access control test
def default_control_test(user):
    """Returns true if:
         * Auth isn't needed or
         * The user is a super user or
         * In the right translators group
    """
    if not getattr(settings, AUTH, True):
        return True
    if not user.is_authenticated():
        return False
    elif user.is_superuser and user.is_staff:
        return True
    return user.groups.filter(name='translators').exists()

