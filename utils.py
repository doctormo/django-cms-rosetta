
from django.utils.importlib import import_module

import types

from .conf import settings


def get_meta_variable(name, *args):
    """Returns a callable variable for the given setting"""
    variable = getattr(settings, name, *args)
    if isinstance(variable, str):
        (module, func) = variable.rsplit('.', 1)
        variable = getattr(import_module(module), func)
    return variable

def get_function_for(name, *args):
    variable = get_meta_variable(name, *args)
    if not callable(variable):
        raise AttributeError("%s isn't a callable variable!" % variable)
    return variable

def get_class_for(name, *args):
    variable = get_meta_variable(name, *args)
    if type(variable) is types.ClassType:
        raise AttributeError("%s isn't a callable variable!" % variable)
    return variable

