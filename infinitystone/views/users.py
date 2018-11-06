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
from luxon import register
from luxon import router
from luxon import db
from luxon.utils.sql import build_where
from luxon.helpers.access import validate_access
from luxon.helpers.api import raw_list, sql_list, obj
from luxon.exceptions import DuplicateError, AccessDeniedError

from infinitystone.models.users import infinitystone_user
from infinitystone.models.tenants import infinitystone_tenant
from infinitystone.models.user_roles import infinitystone_user_role
from infinitystone.utils.auth import (get_user_roles,
                                      get_role_id,
                                      domains,
                                      tenants,
                                      tenant_or_sub,
                                      get_sub_tenants,
                                      hash_password,
                                      get_all_roles)

from luxon import GetLogger

log = GetLogger(__name__)

@register.resources()
class Users(object):
    def __init__(self):
        # Normal Tachyonic uers.
        router.add('GET', '/v1/user/{id}', self.user,
                   tag='users:view')
        router.add('GET', '/v1/users', self.users,
                   tag='users:view')
        router.add('POST', '/v1/user', self.create,
                   tag='users:admin')
        router.add(['PUT', 'PATCH'], '/v1/user/{id}', self.update,
                   tag='users:admin')
        router.add('DELETE', '/v1/user/{id}', self.delete,
                   tag='users:admin')

        router.add('GET',
                   '/v1/access/',
                   self.access,
                   tag='users:admin')
        router.add('GET',
                   '/v1/access/{domain}',
                   self.access,
                   tag='users:admin')
        router.add('GET',
                   '/v1/access/{domain}/{tenant_id}',
                   self.access,
                   tag='users:admin')

        router.add('GET', '/v1/user_roles', self.get_roles,
                   tag='login')
        router.add('GET', '/v1/user_roles/{user_id}', self.get_roles,
                   tag='users:admin')

        router.add('POST', '/v1/user_roles/{user_id}/{role}',
                   self.set_role,
                   tag='users:admin')
        router.add('POST', '/v1/user_roles/{user_id}/{role}/{domain}',
                   self.set_role,
                   tag='users:admin')
        router.add('POST',
                   '/v1/user_roles/{user_id}/{role}/{domain}/{tenant_id}',
                   self.set_role,
                   tag='users:admin')

        router.add('DELETE', '/v1/user_roles/{user_id}/{role_id}',
                   self.rm_role,
                   tag='users:admin')

        # Services Users
        router.add('GET', '/v1/user/{id}/{tag}', self.user,
                   tag='internal')
        router.add('GET', '/v1/users/{tag}', self.users,
                   tag='internal')
        router.add('POST', '/v1/user/{tag}', self.create,
                   tag='internal')
        router.add(['PUT', 'PATCH'], '/v1/user/{id}/{tag}', self.update,
                   tag='internal')
        router.add('DELETE', '/v1/user/{id}/{tag}', self.delete,
                   tag='internal')

    def user(self, req, resp, id, tag='tachyonic'):
        return obj(req, infinitystone_user, sql_id=id,
                   tag=tag, hide=('password',))

    def users(self, req, resp, tag='tachyonic'):
        return sql_list(req, 'infinitystone_user',
                        ('id', 'username', 'name',),
                        tag=tag)

    def create(self, req, resp, tag='tachyonic'):
        user = obj(req, infinitystone_user,
                   tag=tag, hide=('password',))
        if req.json.get('password') is not None:
            user['password'] = hash_password(req.json['password'],
                                             tag)
        user.commit()
        return user

    def update(self, req, resp, id, tag='tachyonic'):
        user = obj(req, infinitystone_user, sql_id=id,
                   tag=tag, hide=('password',))
        if req.json.get('password') is not None:
            user['password'] = hash_password(req.json['password'],
                                             tag)

        user.commit()
        return user

    def delete(self, req, resp, id, tag='tachyonic'):
        user = obj(req, infinitystone_user, sql_id=id,
                   tag=tag)
        user.commit()


    def _get_roles(self, req, user_id=None):
        if not user_id:
            user_id = req.credentials.user_id
        else:
            user = infinitystone_user()
            user.sql_id(user_id)
            validate_access(req, user, tag='tachyonic')

        roles = []

        for role in get_user_roles(user_id):
            role = {"id": role['id'],
                    "role": role['role'],
                    "domain": role['domain'],
                    "tenant_id": role['tenant_id'],
                    "tenant": role['tenant']}
            roles.append(role)

        return roles

    def _access(self, user_roles, domain=None,
                tenant_id=None):

        roles = []
        # For Sub level Tenants
        if tenant_id:
            tenants = get_sub_tenants(tenant_id)

        for user_role in user_roles:
            role = user_role['role']

            # GLOBAL ROLES
            if (user_role['domain'] is None and
                    user_role['tenant_id'] is None):
                if user_role['role'] == 'Root':
                    return get_all_roles()
                elif user_role['role'] not in roles:
                        roles.append(role)
            # Domain Roles
            if (user_role['domain'] == domain and
                    user_role['tenant_id'] is None):
                if user_role['role'] == 'Root':
                    return get_all_roles()
                elif user_role['role'] not in roles:
                        roles.append(role)
            elif domain is not None and tenant_id is not None:
                # Domain level Tenant Roles
                if (user_role['domain'] == domain and
                        user_role['tenant_id'] in tenants):
                    if user_role['role'] == 'Root':
                        return get_all_roles()
                    elif user_role['role'] not in roles:
                            roles.append(role)

        return roles

    def access(self, req, resp, domain=None, tenant_id=None):
        user_roles = self._get_roles(req)
        roles = self._access(user_roles, domain, tenant_id)
        for item, role in enumerate(roles):
            roles[item] = { 'role': role }
        return raw_list(req, roles, rows=len(roles))

    def get_roles(self, req, resp, user_id=None):
        roles = self._get_roles(req, user_id)

        return raw_list(req, roles, rows=len(roles), context=False)

    def set_role(self, req, resp, user_id,
                  role, domain=None, tenant_id=None):
        role_id = get_role_id(role)
        current_roles = self._get_roles(req)

        # Ensure Tenant in Domain.
        if tenant_id:
            tenant = infinitystone_tenant()
            tenant.sql_id(tenant_id)
            validate_access(req, tenant, tag='tachyonic')
            # Important sanity..
            domain = tenant['domain']

        # Check if access to role
        access = self._access(current_roles, domain, tenant_id)
        if role not in access:
            raise AccessDeniedError(access)
            raise AccessDeniedError('Not sufficiant credentials to assign role')

        model = infinitystone_user_role()
        model['role_id'] = role_id
        model['user_id'] = user_id
        model['domain'] = domain
        model['tenant_id'] = tenant_id
        model.commit()

    def rm_role(self, req, resp, user_id, role_id):
        user = infinitystone_user()
        user.sql_id(user_id)
        validate_access(req, user, tag='tachyonic')
        with db() as conn:
            sql = "DELETE FROM infinitystone_user_role"
            where, values = build_where(id=role_id,
                                        user_id=user_id)
            sql += " WHERE %s" % where
            conn.execute(sql, values)
            conn.commit()
