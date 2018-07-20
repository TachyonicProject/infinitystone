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
from luxon import GetLogger
from luxon import register
from luxon import g
from luxon import router
from luxon.exceptions import ValidationError
from luxon.exceptions import AccessDeniedError
from luxon.exceptions import HTTPNotFound
from luxon import db
from luxon.utils.timezone import now
from luxon.utils.sql import build_where

from uuid import uuid4
import json

from infinitystone.utils.auth import user_domains

log = GetLogger(__name__)


def check_unique(conn, id, role, domain, tenant_id):
    """Function to check if user role assignment is unique.

    Args:
        conn (obj): DB connection object.
        id (str): UUID of user.
        role (str): UUID of role.
        domain (str): Name of the domain.
        tenant_id (str): UUID of the tenant.
    """
    sql = "SELECT id FROM infinitystone_user_role WHERE user_id=? AND role_id=? AND "
    vals = [id, role]
    query, addvals = build_where(domain=domain, tenant_id=tenant_id)
    sql += query
    cur = conn.execute(sql, (vals + addvals))
    if cur.fetchone():
        raise ValidationError("Entry for user '%s' role '%s' "
                              "already exists on domain '%s'"
                              " and tenant '%s'."
                              % (id, role, domain, tenant_id))


def check_context_auth(conn, user_id, domain, tenant_id):
    """Verify if users has jurisdiction over requested domain/tenant.

    The default Root user can assign any role to any user.

    Only users with Admin or Root roles are allowed to assign roles to
    users. This function will raise an error if the requesting user is
    not an admin user on the requested domain/tenant.

    Args:
        conn (obj): DB connection object.
        user_id (str): UUID of user.
        domain (str): Name of the domain.
        tenant_id (str): UUID of the tenant.
    """
    req_user_id = g.current_request.credentials.user_id
    if req_user_id != '00000000-0000-0000-0000-000000000000':
        cur = conn.execute("SELECT id FROM infinitystone_role WHERE name=?",
                           ('Administrator',))
        admin_id = cur.fetchone()['id']

        query, vals = build_where(user_id=req_user_id,
                                  domain=domain,
                                  tenant_id=tenant_id)
        query += " AND ('role_id'='00000000-0000-0000-0000-000000000000'"
        query += " OR role_id=?)"
        vals.append(admin_id)

        sql = "SELECT id FROM infinitystone_user_role WHERE " + query
        cur = conn.execute(sql, vals)
        if not cur.fetchone():
            raise AccessDeniedError(
                "User %s not authorized in requested context "
                ": domain '%s', tenant_id '%s'"
                % (req_user_id, domain, tenant_id))


@register.resource('GET', '/v1/rbac/domains', tag='login')
def rbac_domains(req, resp):
    """Supplies a List of available domains.
        Supplies a List of available domains.

        Used when assigning a user's role.
    """
    search = req.query_params.get('term')
    # (@vuader) Because the Root user can and have to be able to
    # assign Roles on ANY domain, and this view is used for that
    # purpose, we need to select ALL domains for the Root user.
    user_id = req.token.user_id
    if user_id == "00000000-0000-0000-0000-000000000000":
        sql = "SELECT name FROM infinitystone_domain"
        with db() as conn:
            cur = conn.execute(sql)
            result = cur.fetchall()
        domains_list = []
        for r in result:
            domains_list.append(r['name'])
    else:
        domains_list = user_domains(req.token.user_id)
    if search is not None:
        filtered = []
        for domain in domains_list:
            if search in domain:
                filtered.append(domain)
        return filtered
    return domains_list


@register.resource('GET', '/v1/rbac/tenants', tag='login')
def rbac_tenants(req, resp):
    """Supplies a List of available tenants.
    Supplies a List of available tenants.

    Used when assigning a user's role.
    """
    user_id = req.token.user_id
    if user_id == "00000000-0000-0000-0000-000000000000":
        sql = "SELECT id as tenant_id,name FROM infinitystone_tenant"
    else:
        sql = "SELECT infinitystone_user_role.tenant_id,name FROM infinitystone_user_role" \
          ",infinitystone_tenant WHERE" \
          " infinitystone_user_role.tenant_id=infinitystone_tenant.id " \
          "AND user_id=?"
    tenants = {}
    with db() as conn:
        cur = conn.execute(sql, user_id)
        for r in cur.fetchall():
            tenants[r['tenant_id']] = r['name']
        return json.dumps(tenants)


@register.resource('GET', '/v1/rbac/roles', tag='login')
def rbac_roles(req, resp):
    """Supplies a List of available roles.
    Supplies a List of available roles.

    Used when assigning a user's role.
    """
    sql = "SELECT id,name FROM infinitystone_role"
    roles = {}
    with db() as conn:
        cur = conn.execute(sql)
        for r in cur.fetchall():
            roles[r['id']] = r['name']
        return json.dumps(roles)


@register.resource('GET', '/v1/rbac/user/{id}', tag='login')
def user_roles(req, resp, id):
    sql = "SELECT infinitystone_user_role.*,infinitystone_tenant.name as tenant_name," \
          "infinitystone_role.name as role_name FROM infinitystone_user_role LEFT JOIN " \
          "infinitystone_tenant" \
          "ON infinitystone_user_role.tenant_id=infinitystone_tenant.id " \
          "LEFT JOIN infinitystone_role" \
          " ON infinitystone_user_role.role_id = infinitystone_role.id " \
          "WHERE user_id=?"
    with db() as conn:
        cur = conn.execute(sql, id)
        result = cur.fetchall()
    return json.dumps(result, indent=4, sort_keys=True, default=str)


@register.resources()
class AddUserRoles():
    def __init__(self):
        router.add('POST', '/v1/rbac/user/{id}/{role}',
                   self.add_user_role, tag="users:admin")
        router.add('POST', '/v1/rbac/user/{id}/{role}/{domain}',
                   self.add_user_role, tag="users:admin")
        router.add('POST', '/v1/rbac/user/{id}/{role}/{domain}/{tenant_id}',
                   self.add_user_role, tag="users:admin")

    def add_user_role(self, req, resp, id, role, domain=None, tenant_id=None):
        """
        Associate role to a user.

        Args:
            id (str): UUID of user.
            role (str): UUID of role.
            domain (str): Name of domain (defaults to None).
                          Use the text "none" to indicate global domain
                          when tenant_id is supplied.
            tenant_id (str): UUID of tenant (defaults to None).

        Example return data:

        .. code-block:: json

            {
                "id": "e729af96-5672-4669-b4a1-6251493a67fa",
                "user_id": "e95ec7b1-4f0f-4c70-991f-4bb1bec6a524",
                "role_id": "08034650-1438-4e56-b5a8-674ede74fe83",
                "domain": "default",
                "tenant_id": null
            }
        """
        if domain is not None and domain.lower() == "none":
            domain = None
        with db() as conn:
            check_context_auth(conn, id, domain, tenant_id)
            # Even though we have unique constraint, sqlite
            # does not consider null as unique. ref:
            # https://goo.gl/JmjT5G
            # So need to manually check that.
            check_unique(conn, id, role, domain, tenant_id)

            sql = "INSERT INTO infinitystone_user_role " \
                  "(`id`,`role_id`,`tenant_id`,`user_id`," \
                  "`domain`,`creation_time`) " \
                  "VALUES (?,?,?,?,?,?)"
            user_role_id = str(uuid4())
            conn.execute(sql, (user_role_id, role, tenant_id,
                               id, domain, now()))
            conn.commit()
            user_role = {"id": user_role_id,
                         "user_id": id,
                         "role_id": role,
                         "domain": domain,
                         "tenant_id": tenant_id}
            return json.dumps(user_role, indent=4)


@register.resources()
class RmUserRoles():
    def __init__(self):
        router.add('DELETE', '/v1/rbac/user/{id}/{role}',
                   self.rm_user_role, tag="users:admin")
        router.add('DELETE', '/v1/rbac/user/{id}/{role}/{domain}',
                   self.rm_user_role, tag="users:admin")
        router.add('DELETE',
                   '/v1/rbac/user/{id}/{role}/{domain}/{tenant_id}',
                   self.rm_user_role, tag="users:admin")

    def rm_user_role(self, req, resp, id, role, domain=None, tenant_id=None):
        """
        Remove a role associated to a user.

        Args:
            id (str): UUID of user.
            role (str): UUID of role.
            domain (str): Name of domain (defaults to None).
                          Use the text "none" to indicate global domain
                          when tenant_id is supplied.
            tenant_id (str): UUID of tenant (defaults to None).

        Returns:
            200 OK with blank body if successful
            404 Not Found if now entry was affected

        """
        if domain and domain.lower() == "none":
            domain = None

        with db() as conn:
            where = {'user_id': id,
                     'role_id': role,
                     'tenant_id': tenant_id,
                     'domain': domain}
            query, vals = build_where(**where)
            sql = "DELETE FROM infinitystone_user_role WHERE " + query
            cur = conn.execute(sql, vals)
            conn.commit()
            if not cur.rowcount:
                raise HTTPNotFound("No entry for %s" % where)
                # Not Returning any body - 200 OK says it all.
