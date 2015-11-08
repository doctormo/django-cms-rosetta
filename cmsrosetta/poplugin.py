#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Base classes for translation plugins for your application.
"""

class TranslationPlugin(dict):
    """Base class to list available translatable items"""
    def __init__(self, languages):
        self.languages = languages
        self.generate()

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError("Locale id/name used: %s" % key)
        return dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if not len(self):
            self.generate()
        if key in self.languages:
            return [ b[key] for (a,b) in self.items() ]
        return dict.__getitem__(self, key)

    def __iter__(self):
        if not len(self):
            self.generate()
        return dict.__iter__(self)

    def slug(self):
        raise NotImplementedError("Slug is required for translation plugins")

    def generate(self):
        raise NotImplementedError("Generate is required for translation plugins")


class TranslationDirectory(list):
    name = 'None'

    def __init__(self, languages):
        self.languages = languages

    def generate(self):
        raise NotImplementedError("Generate is required for translation directories")

    def __iter__(self):
        # THIS LOOKS BROKEN XXX
        for lang in self.languages:
            yield self[lang]

    def __getitem__(self, key):
        if not len(self):
            self._generate_all()
        index  = list(self.languages).index(key)
        pofile = list.__getitem__(self, index)
        if pofile.is_stale:
            self[index] = self.generate(key)
        return list.__getitem__(self, index)

    def _veriations(self, lang):
        """Generator to return en, en_GB, en_gb, en-gb, en-GB veriations"""
        lang = lang.replace('_', '-')
        if '-' in lang:
            bits = lang.lower().split('-', 1)
            for sep in '-_':
                yield bits[0] + sep + bits[1]
                yield bits[0] + sep + bits[1].upper()
        else:
            yield lang

    def _generate_all(self):
        for lang in self.languages:
            self.append(self.generate(lang))


