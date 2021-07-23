#! /usr/bin/env python3
# Copyright 2021 Tom SF Haines

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import base64



secret1 = base64.urlsafe_b64encode(os.urandom(128)).decode('utf8') # 1024 bits!
secret2 = base64.b64encode(os.urandom(128)).decode('utf8') # "
with open('secret.txt', 'w') as fout:
  fout.write(secret1)
  fout.write('\n')
  fout.write(secret2)

os.chmod('secret.txt', 0o600)
