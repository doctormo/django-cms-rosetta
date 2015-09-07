
from polib import POEntry
from hashlib import md5
from six import text_type as text

def _nls(orig, new):
    """Fixes submitted translations by filtering carriage returns and pairing
        newlines at the begging and end of the translated string with the original
    """
    if 0 == len(orig) or 0 == len(new):
        return new
    if "\r" in new and "\r" not in orig:
        new = new.replace("\r", '')
    if "\n" == orig[0] and "\n" != new[0]:
        new = "\n" + new
    elif "\n" != orig[0] and "\n" == new[0]:
        new = new.lstrip()
    if "\n" == orig[-1] and "\n" != new[-1]:
        new = new + "\n"
    elif "\n" != orig[-1] and "\n" == new[-1]:
        new = new.rstrip()
    return new

def get_md5hash(self):
    c = text(self.msgid) + text(self.msgstr) + text(self.msgctxt)
    return md5(c.encode('utf8')).hexdigest()

def set_msg(self, msg):
    if isinstance(msg, list):
        for (x, d) in enumerate(self.msgstr_plural):
            msg[x] = _nls(d, msg[x])
            if msg[x] != d:
                self.msgstr_plural[x] = msg[x]
                self.updated = True
    else:
        msg = _nls(self.msgstr, msg)
        if msg != self.msgstr:
            self.msgstr = msg
            self.updated = True

def set_flag(self, flag, value):
    (a,b) = (flag in self.flags, value)
    if a and not b:
        self.flags.remove(flag)
        self.updated = True
    elif b and not a:
        self.flags.append(flag)
        self.updated = True

def is_short(self):
    return len(self.msgid) < 40 and '\n' not in self.msgid

def occurrences_trim(self):
    ret = []
    for fn,lineno in self.occurrences:
        fn = fn.split('django/contrib/')[-1].split('site-packages/')[-1]
        ret.append((fn, lineno))
    return ret

# Monkey patch for unique-id for each entry
POEntry.md5hash = property(get_md5hash)
POEntry.set_flag = set_flag
POEntry.set_msg = set_msg
POEntry.is_short = is_short
POEntry.occurrences_trim = occurrences_trim
