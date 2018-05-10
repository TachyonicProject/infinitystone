#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import argparse
import site

if not sys.version_info >= (3,5):
    print('Requires python version 3.5 or higher')
    exit()

from luxon import g
from luxon.core.handlers.script import Script
from luxon.utils.encoding import if_bytes_to_unicode
from luxon import register_resource
from luxon import register_middleware
from luxon.middleware.script.auth import Auth
from luxon.utils.formatting import format_obj

from tachyonic import metadata

@register_resource('SCRIPT', 'endpoints')
def endpoints(req, resp):
    group = req.parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l',
                       action='store_true',
                       dest='list_endpoints',
                       default=False,
                       help='List endpoints')
    group.add_argument('-d',
                       dest='delete_id',
                       help='Delete Endpoint by ID')
    group.add_argument('-c',
                       dest='endpoint_name',
                       help='Create Endpoint')

    req.parser.add_argument('--uri',
                            help='URI for endpoint',
                            default=None)
    req.parser.add_argument('--interface',
                            help='Inteface (public|internal|admin)',
                            default='public')
    req.parser.add_argument('--region',
                            help='Region name for endpoint',
                            default='default')
    args = req.parser.parse_args()
    if args.endpoint_name is not None:
        res = g.api.new_endpoint(args.endpoint_name,
                                 args.interface,
                                 args.region,
                                 args.uri)
        return format_obj(res.json)
    elif args.list_endpoints is True:
        res = g.api.list_endpoints()
        return format_obj(res.json)
    elif args.delete_id is not None:
        res = g.api.delete_endpoint(args.delete_id)

def main(argv):
    script = Script(__name__, app_root='.')
    register_middleware(Auth)

    val = script(metadata).read()
    if val:
        val = if_bytes_to_unicode(val)
        print(val)


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    entry_point()
