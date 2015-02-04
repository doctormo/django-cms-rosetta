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
Test the html parsing
"""

import unittest
import sys
sys.path.insert(0, '../')

try:
    from test import test_support
except ImportError:
    from test import support as test_support


from htmlutil import PotParser

class Html2PoTestCase(unittest.TestCase):
    """Test our custom html to po code."""
    def setUp(self):
        self.parser = PotParser()

    def _t(self, body, result):
        self.assertEqual(self.parser.parse(body), result)

    # Non-splitting
    test_01_plaintext  = lambda self: self._t("No HTML in Text", {'': 'No HTML in Text'})
    test_02_taginclude = lambda self: self._t("Some <b>HTML</b> Text", {'': 'Some <b>HTML</b> Text'})
    test_03_tagattr    = lambda self: self._t("A <b id=\"pk\">to</b> me", {'': "A <b id=\"pk\">to</b> me"})
    test_04_tagclean   = lambda self: self._t("A <b  id='pk' >to</b > me", {'': "A <b id=\"pk\">to</b> me"})
    test_05_escapes    = lambda self: self._t("This has &amp;le html", {'': "This has &le html"})
    
    # Splitting tests
    test_20_paragraphs = lambda self: self._t("<p>One</p><p>Two</p>", {'p-1': 'One', 'p-2': 'Two'})
    test_21_divs       = lambda self: self._t("<div>One</div><div>Two</div>", {'div-1': 'One', 'div-2': 'Two'})
    test_22_levels     = lambda self: self._t("<div>One<p>Two</p>Three</div>", {'div-1': 'One{{ div-p-1 }}Three', 'div-p-1': 'Two'})
    test_23_anchor     = lambda self: self._t("<p>Something <a href=''>Linked</a> here</p>", {'p-a-1': u'Linked', 'p-1': u'Something {{ p-a-1 }} here'})
    test_24_image      = lambda self: self._t("<p>An <img src='foo'/> goes here</p>", {'p-1': u'An {{ p-img-1 }} goes here'})

if __name__ == '__main__':
    test_support.run_unittest( Html2PoTestCase )

