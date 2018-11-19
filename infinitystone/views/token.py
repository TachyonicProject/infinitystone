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
from luxon import register
from luxon import router
from luxon.utils.imports import get_class

from infinitystone.helpers.auth import localize
from infinitystone.helpers.users import get_user_id
from infinitystone.helpers.roles import get_context_roles
from infinitystone.helpers.tenants import get_tenant_domain


@register.resources()
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
        router.add('GET', '/v1/token', self.get)
        router.add('POST', '/v1/token', self.post)
        router.add('PATCH', '/v1/token', self.patch)

    def get(self, req, resp):
        return req.credentials

    def post(self, req, resp):
        request_object = req.json
        method = request_object.get('method', 'password')
        driver = g.app.config.get('auth', 'driver')
        driver = get_class(driver)()
        if hasattr(driver, method):
            method = getattr(driver, method)
        else:
            raise ValueError(
                "'%s' authentication method not supported" % method
            )

        credentials = request_object.get('credentials')
        username = request_object.get('username')
        domain = request_object.get('domain')
        if isinstance(credentials, dict):
            method(username, domain, credentials=credentials)
        elif credentials is None:
            raise ValueError("Require 'credentials'")
        else:
            raise ValueError("Invalid 'credentials' provided")

        # Creat User locally if not existing
        localize(username, domain)
        # Get User_id
        user_id = get_user_id(username, domain)
        # Get Roles
        global_roles = get_context_roles(user_id, None)
        domain_roles = get_context_roles(user_id, domain)
        # Set roles in token
        req.credentials.new(user_id, username=username, domain=domain)
        req.credentials.roles = domain_roles + global_roles

        return req.credentials

    def patch(self, req, resp):
        request_object = req.json
        domain = request_object.get('domain')
        tenant_id = request_object.get('tenant_id')
        user_id = req.credentials.user_id
        if tenant_id is not None:
            req.credentials.domain = get_tenant_domain(tenant_id)
            req.credentials.tenant_id = tenant_id
            req.credentials.roles = get_context_roles(user_id)
            req.credentials.roles = get_context_roles(user_id,
                                                      req.credentials.domain)
            req.credentials.roles = get_context_roles(user_id,
                                                      req.credentials.domain,
                                                      tenant_id)

        elif domain is not None:
            req.credentials.domain = domain
            req.credentials.roles = get_context_roles(user_id)
            req.credentials.roles = get_context_roles(user_id, domain)
            
        return req.credentials
