from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re
from django.template import Node
import six

from collections import OrderedDict, defaultdict

register = template.Library()

# We want to over-ride the pagination template, believe it or not
# this is the best way to re-use as much of the paginaiton code.
from pagination.templatetags.pagination_tags import paginate as paginate_cms, do_autopaginate
register.inclusion_tag('rosetta/pagination.html', takes_context=True)(paginate_cms)
register.tag('autopaginate', do_autopaginate)

rx = re.compile(r'(%(\([^\s\)]*\))?[sd])')

def progressbar(context, progress):
    try:
        to_return = OrderedDict((a, dict(name=b, groups=c, total=d)) for (a,b,c,d) in progress)
    except ValueError:
        raise ValueError("Corrupt progress structure, got: %s " % str(progress))

    for v in to_return.values():
        for group in v.get('groups', None) or []:
            if not group in to_return:
                to_return[group] = dict(name=group.title(), total=0)
            to_return[group]['total'] += v['total']
    
    if 'all' in to_return:
        total = to_return['all']['total']
        for item in to_return.values():
            item['percent'] = float(item['total']) / total * 100

    to_return['keys'] = to_return
    return to_return

register.inclusion_tag('rosetta/progress.html', takes_context=True)(progressbar)

def format_message(message):
    return mark_safe(rx.sub('<code>\\1</code>', escape(message).replace(r'\n', '<br />\n')))
format_message = register.filter(format_message)


def lines_count(message):
    return 1 + sum([len(line) / 50 for line in message.split('\n')])
lines_count = register.filter(lines_count)


def mult(a, b):
    return int(a) * int(b)
mult = register.filter(mult)


def minus(a, b):
    try:
        return int(a) - int(b)
    except:
        return 0
minus = register.filter(minus)


def gt(a, b):
    try:
        return int(a) > int(b)
    except:
        return False
gt = register.filter(gt)


def do_incr(parser, token):
    args = token.split_contents()
    if len(args) < 2:
        raise SyntaxError("'incr' tag requires at least one argument")
    name = args[1]
    if not hasattr(parser, '_namedIncrNodes'):
        parser._namedIncrNodes = {}
    if not name in parser._namedIncrNodes:
        parser._namedIncrNodes[name] = IncrNode(0)
    return parser._namedIncrNodes[name]
do_incr = register.tag('increment', do_incr)


class IncrNode(template.Node):
    def __init__(self, init_val=0):
        self.val = init_val

    def render(self, context):
        self.val += 1
        return six.text_type(self.val)


def is_fuzzy(message):
    return message and hasattr(message, 'flags') and 'fuzzy' in message.flags
is_fuzzy = register.filter(is_fuzzy)


class RosettaCsrfTokenPlaceholder(Node):
    def render(self, context):
        return mark_safe(u"<!-- csrf token placeholder -->")


def rosetta_csrf_token(parser, token):
    try:
        from django.template.defaulttags import csrf_token
        return csrf_token(parser, token)
    except ImportError:
        return RosettaCsrfTokenPlaceholder()
rosetta_csrf_token = register.tag(rosetta_csrf_token)
