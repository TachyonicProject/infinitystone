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
from luxon import g
from luxon import GetLogger
from luxon.exceptions import AccessDenied
from luxon import register_resources

log = GetLogger(__name__)

@register_resources()
class Token(object):
    """Token Middleware.

    Validates token and sets request.token object.

    Luxon tokens use PKI. Its required to have the private key to sign
    new tokens on the tachyonic api. Endpoints will require the public cert
    to validate tokens authenticity.

    The tokens should be stored in the application root. Usually where the wsgi
    file is located.

    Creating token:
        openssl req  -nodes -new -x509  -keyout token.key -out token.cert
    """
    def __init__(self):
        g.router.add('GET', '/v1/token', self.get)
        g.router.add('POST', '/v1/token', self.post)
        g.router.add('PATCH', '/v1/token', self.patch, tag='login')

    def get(self, req, resp):
        return req.token

    def post(self, req, resp):
        request_object = req.json
        req.token.login(request_object.get('username',
                                           None),
                    request_object.get('password', None),
                    request_object.get('domain', None))
        return req.token

    def patch(self, req, resp):
        request_object = req.json
        req.token.scope_token(req.token.token['token'],
                              request_object.get('domain'),
                              request_object.get('tenant_id'))
        return req.token
