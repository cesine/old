# Copyright 2013 Joel Dunham
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""This script contains the imports and globals needed to interact with and old
app via the command line.

See https://groups.google.com/forum/?fromgroups=#!topic/pylons-discuss/kMR9xhIPpD0
"""

from paste.deploy import appconfig
from pylons import config
from old.config.environment import load_environment
import old.model as model
from old.model.meta import Session
import old.lib.helpers as h

conf = appconfig('config:test.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# forms = Session.query(model.Form).all()
# etc. ...

print type(h.dateString2date('2012-01-01'))