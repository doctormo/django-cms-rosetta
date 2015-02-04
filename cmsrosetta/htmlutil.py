#
# Copyright (C) 2015  Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Cut through html and find translations in them.
"""

from HTMLParser import HTMLParser
from collections import defaultdict

class PotParser(HTMLParser):
    BODY_TAGS = ('b', 'i', 'u', 'strong', 'em', 'small', 'mark', 'del', 'ins', 'sub', 'sup', 'a')

    def parse(self, body):
        self._current_tags = []
        self._tag_indexes = defaultdict(int)
        self._texts = defaultdict(str)
        self.feed(body)
        return dict(self._texts)

    def handle_starttag(self, tag, attrs):
        if tag in self.BODY_TAGS:
            # Add 'body' tags to the text, include in translation
            attr = ' '.join("%s=\"%s\"" % (name, value) for (name, value) in attrs)
            self._texts[self._current_tag_id] += ("<%s%s%s>" % (tag, attr and ' ', attr))
        else:
            # Any other tags are 'splitters' which cleave the text into a new translation.
            self._current_tags.append(tag)
            # We append a counter here to keep tag chains unique
            self._tag_indexes[self._current_tag] += 1

    def handle_endtag(self, tag):
        if tag in self.BODY_TAGS:
            self._texts[self._current_tag_id] += ("</%s>" % tag)
        elif tag in self._current_tags:
            i = self._current_tags.index(tag, -1)
            self._current_tags = self._current_tags[:i]

    def handle_data(self, data):
        self._texts[self._current_tag_id] += data 


    @property
    def _current_tag(self):
        """The tag parts without the counter id suffix"""
        return '-'.join(self._current_tags)

    @property
    def _current_id(self):
        """Return the counter suffix only for this tag block"""
        return self._tag_indexes[self._current_tag]

    @property
    def _current_tag_id(self):
        "Returns the combined tag and counter id suffix for this text block"
        if self._current_id and self._current_tag:
            return "%s-%d" % (self._current_tag, self._current_id)
        return ''

