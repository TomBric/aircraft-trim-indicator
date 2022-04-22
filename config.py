"""
# BSD 3-Clause License
# Copyright (c) 2022, Thomas Breitbach https://github.com/TomBric
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

Modified from
https://github.com/dwighthubbard
Thanks
"""

import json
import os

default_config = 'etc/trim_config.json'

def load(config_file=None):
    if config_file is None:
        config_file = default_config
    try:
        with open(config_file) as f:
            return json.loads(f.read())
    except OSError:
        pass
    return {}


def save(values, config_file=None):
    if not config_file:
        config_file = default_config

    try:
        os.mkdir('etc')
    except OSError:
        pass

    with open(config_file, 'wb') as f:
        f.write(json.dumps(values))


def get(key, config_file=None):
    return load(config_file=config_file).get(key, '')


def set(key, value, config_file=None):
    values = load(config_file=config_file)
    values[key] = value
    save(values, config_file=config_file)


def delete(key, config_file=None):
    values = load(config_file=config_file)
    del values[key]
    save(values, config_file=config_file)


def list_settings(config_file=None):
    settings = load(config_file=config_file)
    keys = list(settings.keys())
    keys.sort()
    for key in keys:
        print('%s=%s' % (key, settings[key]))