
from django.utils.importlib import import_module

import types
import settings


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

def fix_nls(in_, out_):
    """Fixes submitted translations by filtering carriage returns and pairing
        newlines at the begging and end of the translated string with the original
    """
    if 0 == len(in_) or 0 == len(out_):
        return out_

    if "\r" in out_ and "\r" not in in_:
        out_ = out_.replace("\r", '')

    if "\n" == in_[0] and "\n" != out_[0]:
        out_ = "\n" + out_
    elif "\n" != in_[0] and "\n" == out_[0]:
        out_ = out_.lstrip()

    if "\n" == in_[-1] and "\n" != out_[-1]:
        out_ = out_ + "\n"
    elif "\n" != in_[-1] and "\n" == out_[-1]:
        out_ = out_.rstrip()
    return out_

