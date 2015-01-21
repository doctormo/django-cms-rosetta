#!/usr/bin/env python
#
# Copyright (C) 2014 Martin Owens
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from setuptools import setup, find_packages

from cmsrosetta import __version__

setup(
    name         = 'django-cmsrosetta',
    version      = __version__,
    url          = 'https://code.launchpad.net/~doctormo',
    license      = 'AGPLv3',
    platforms    = ['OS Independent'],
    description  = "Translation django-app for pot files, inclusing django-cms",
    author       = 'Martin Owens',
    author_email = 'doctormo@gmail.com',
    packages     = find_packages(),
    install_requires = [
      'setuptools',
      'polib>=1.0.4',
      'django-cms>=3.0',
      'django-haystack>=2.0',
      'django-request-tree>=0.8',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
