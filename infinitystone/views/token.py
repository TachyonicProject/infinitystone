# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Christiaan Frans Rademan <chris@fwiw.co.za>.
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
from luxon import db
from luxon import register
from luxon import router
from luxon.utils.imports import get_class
from luxon.exceptions import HTTPForbidden
from luxon.utils.timezone import to_utc

from infinitystone.helpers.auth import localize, user_tenant
from infinitystone.helpers.users import get_user_id
from infinitystone.helpers.roles import get_context_roles
from infinitystone.helpers.tenants import get_tenant_domain


@register.resources()
class Token(object):
    """Token Authentication.

    Validates token and sets request.token object.

    Luxon tokens use RSA Keys. Its required to have the private key to sign
    new tokens on the tachyonic api. Endpoints will require the public key
    to validate tokens authenticity.
    """
    def __init__(self):
        router.add('GET', '/v1/token', self.get)
        router.add('POST', '/v1/token', self.post)
        router.add('PUT', '/v1/token', self.put)
        router.add('PATCH', '/v1/token', self.patch)

    def get(self, req, resp):
        return req.credentials

    def put(self, req, resp):
        username = req.credentials.username
        domain = req.credentials.user_domain
        user_id = get_user_id(username, domain)
        with db() as conn:
            sql = "SELECT username, creation_time FROM infinitystone_user"
            sql += " WHERE id = %s AND enabled = '1'"
            user = conn.execute(sql, user_id).fetchone()
        if user:
            if user['creation_time'] > to_utc(
                    req.credentials._credentials['loginat']):
                raise HTTPForbidden('User account suspended or invalid')
            localize(username, domain, req.credentials.user_region,
                     req.credentials.user_confederation, user_id)
            req.credentials.extend()
            return req.credentials
        else:
            raise HTTPForbidden('User account suspended or invalid')

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
            metadata = method(username, domain, credentials=credentials)
        elif credentials is None:
            raise ValueError("Require 'credentials'")
        else:
            raise ValueError("Invalid 'credentials' provided")

        # Create User locally if not existing
        localize(username, domain)
        # Get User_id
        user_id = get_user_id(username, domain)
        # Get Roles
        global_roles = get_context_roles(user_id, None)
        domain_roles = get_context_roles(user_id, domain)
        # Set roles in token
        req.credentials.new(user_id, username=username, domain=domain,
                            region=g.app.config.get(
                                'auth',
                                'region',
                                fallback='Region1'),
                            confederation=g.app.config.get(
                                'auth',
                                'confederation',
                                fallback='Confederation1'),
                            metadata=metadata)
        req.credentials.roles = domain_roles + global_roles
        if len(req.credentials.roles) == 0:
            usr_cust_tenants = user_tenant(user_id, 'Customer')
            if len(usr_cust_tenants) == 1:
                req.credentials.domain = get_tenant_domain(
                    usr_cust_tenants[0])
                req.credentials.tenant_id = usr_cust_tenants[0]
                req.credentials.roles = get_context_roles(
                    user_id,
                    req.credentials.domain,
                    usr_cust_tenants[0])
            else:
                try:
                    req.credentials.default_tenant_id = usr_cust_tenants[0]
                except IndexError:
                    pass

        return req.credentials

    def patch(self, req, resp):
        request_object = req.json
        domain = request_object.get('domain')
        tenant_id = request_object.get('tenant_id')
        user_id = req.credentials.user_id
        username = req.credentials.username
        if tenant_id is not None:
            # Its important to find tenants domain, required by Photonic.
            # Since you can select global tenants that may be within a specific
            # domain prior to scoping the domain.
            req.credentials.domain = get_tenant_domain(tenant_id)

            req.credentials.tenant_id = tenant_id
            localize(username, req.credentials.user_domain,
                     req.credentials.user_region,
                     req.credentials.user_confederation,
                     user_id)
            req.credentials.roles = get_context_roles(user_id)
            req.credentials.roles = get_context_roles(user_id,
                                                      req.credentials.domain)
            req.credentials.roles = get_context_roles(user_id,
                                                      req.credentials.domain,
                                                      tenant_id)

        elif domain is not None:
            req.credentials.domain = domain
            localize(username, req.credentials.user_domain,
                     req.credentials.user_region,
                     req.credentials.user_confederation, user_id)
            req.credentials.roles = get_context_roles(user_id)
            req.credentials.roles = get_context_roles(user_id, domain)

        return req.credentials
