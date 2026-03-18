# wings-core
# Copyright (C) 2026 fxllingstar on GitHub
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
from setuptools import setup

setup(
    name='wings-core',
    version='1.0.2',
    py_modules=['wings_core'], # This looks for wings_core.py
    install_requires=[
        'requests',
        'flask',
    ],
    entry_points={
        'console_scripts': [
            'wings-core=wings_core:main', # This creates the wings-core command
        ],
    },
)
from setuptools import setup