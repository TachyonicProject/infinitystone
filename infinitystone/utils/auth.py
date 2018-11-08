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

from luxon import db
from luxon.utils.password import valid as is_valid_password
from luxon.utils.cast import to_list
from luxon.exceptions import AccessDeniedError
from infinitystone.models.users import infinitystone_user
from luxon.helpers.api import sql_list, obj
from luxon import constants as const
from luxon.utils.password import hash


def hash_password(password, tag):
    if tag == 'tachyonic':
        # DEFAULT BLOWFISH BCRYPT
        return hash(password)
    else:
        # DEFAULT CRYPT SHA512
        return hash(password, const.SHA512)



def localize(tag, username, domain):
    with db() as conn:
        values = [tag, username, ]
        sql = 'SELECT username FROM infinitystone_user'
        sql += ' WHERE'
        sql += ' tag = %s'
        sql += ' AND username = %s'
        if domain is not None:
            sql += ' AND domain = %s'
            values.append(domain)
        else:
            sql += ' AND domain IS NULL'
        result = conn.execute(sql,
                              values).fetchall()

        if len(result) == 0:
            if domain is not None:
                conn.execute('INSERT INTO infinitystone_user' +
                             ' (tag, domain, username)' +
                             ' VALUES' +
                             ' (%s, %s, %s)',
                             (tag, domain, username))
            else:
                conn.execute('INSERT INTO infinitystone_user' +
                             ' (tag, username)' +
                             ' VALUES' +
                             ' (%s, %s)',
                             (tag, username))

            conn.commit()


def get_user_id(tag, username, domain=None):
    with db() as conn:
        values = [tag, username, ]
        sql = 'SELECT id FROM infinitystone_user'
        sql += ' WHERE'
        sql += ' tag = %s'
        sql += ' AND username = %s'
        if domain is not None:
            sql += ' AND domain = %s'
            values.append(domain)
        else:
            sql += ' AND domain IS NULL'
        result = conn.execute(sql,
                              values).fetchall()
        if len(result) > 0:
            return result[0]['id']
        else:
            raise ValueError('User not found')

def get_all_roles():
    with db() as conn:
        roles = []
        sql = 'SELECT name FROM infinitystone_role'
        result = conn.execute(sql).fetchall()
        for role in result:
            roles.append(role['name'])
        return roles


def get_role_id(role):
    with db() as conn:
        sql = 'SELECT id FROM infinitystone_role'
        sql += ' WHERE'
        sql += ' name = %s'
        result = conn.execute(sql,
                              role).fetchone()
        if result:
            return result['id']
        else:
            raise ValueError('Role not found')

def get_tenant_domain(tenant_id):
    with db() as conn:
        sql = 'SELECT domain FROM infinitystone_tenant'
        sql += ' WHERE'
        sql += ' id = %s'
        result = conn.execute(sql,
                              tenant_id).fetchone()
        if result:
            return result['domain']

def get_sub_tenants(tenant_id):
    tenants = []

    tenant = tenant_id

    while True:
        tenant = tenant_or_sub(tenant)
        if tenant in tenants:
            break
        tenants.append(tenant)

    if tenant_id not in tenants:
        tenants.append(tenant_id)

    return tenants


def tenant_or_sub(tenant_id):
    with db() as conn:
        sql = 'SELECT tenant_id FROM infinitystone_tenant'
        sql += ' WHERE'
        sql += ' id = %s'
        result = conn.execute(sql,
                              tenant_id).fetchone()
        if result and result['tenant_id']:
            return result['tenant_id']
        elif result and not result['tenant_id']:
            return tenant_id

def get_domains():
    with db() as conn:
        crsr = conn.execute('SELECT * FROM infinitystone_domain')
        return crsr.fetchall()


def get_user_groups(user_id):
    if user_id is None:
        # NOTE(cfrademan): SHORT-CIRCUIT - google is your friend.
        return []

    with db() as conn:
        query = 'SELECT' + \
                ' infinitystone_user_group.id AS id,' + \
                ' infinitystone_user_group.priority AS priority,' + \
                ' infinitystone_group.name AS name' + \
                ' FROM' + \
                ' infinitystone_user_group LEFT JOIN infinitystone_group ON' + \
                ' infinitystone_user_group.group_id = infinitystone_group.id' + \
                ' WHERE infinitystone_user_group.user_id = %s'

        crsr = conn.execute(query, user_id)
        groups = to_list(crsr.fetchall())

    return groups


def get_user_attrs(user_id):
    pass


def get_group_attrs(user_id):
    pass


def get_user_roles(user_id):
    if user_id is None:
        # NOTE(cfrademan): SHORT-CIRCUIT - google is your friend.
        return []

    with db() as conn:
        query = 'SELECT' + \
                ' infinitystone_user_role.id AS assignment_id,' + \
                ' infinitystone_role.name AS role,' + \
                ' infinitystone_user_role.role_id AS role_id,' + \
                ' infinitystone_user_role.id AS id,' + \
                ' infinitystone_user_role.domain AS domain,' + \
                ' infinitystone_user_role.tenant_id AS tenant_id,' + \
                ' infinitystone_tenant.name AS tenant FROM' + \
                ' infinitystone_user_role LEFT JOIN infinitystone_role ON' + \
                ' infinitystone_user_role.role_id = infinitystone_role.id' + \
                ' LEFT JOIN infinitystone_tenant ON' + \
                ' infinitystone_user_role.tenant_id = infinitystone_tenant.id' + \
                ' WHERE infinitystone_user_role.user_id = %s'

        crsr = conn.execute(query, user_id)
        roles = to_list(crsr.fetchall())
        return roles


def user_domains(user_id):
    domains = []
    for role in get_user_roles(user_id):
        domain = role['domain']
        if domain not in domains:
            domains.append(domain)
    return domains


def user_tenants(user_id):
    tenants = {}
    for tenant in get_user_roles(user_id):
        tenant_id = tenant['tenant_id']
        if tenant_id not in tenants:
            if tenant_id is not None:
                tenants[tenant_id] = tenant['tenant']
    return tenants


def get_context_roles(user_id, domain=None, tenant_id=None):
    roles = []
    with db() as conn:
        values = []
        values.append(user_id)
        query = 'SELECT' + \
                ' infinitystone_user_role.id as assignment_id,' + \
                ' infinitystone_user_role.role_id AS role_id,' + \
                ' infinitystone_user_role.domain as domain,' + \
                ' infinitystone_role.name as role,' + \
                ' infinitystone_user_role.tenant_id as tenant_id FROM' + \
                ' infinitystone_user_role LEFT JOIN infinitystone_role ON' + \
                ' infinitystone_user_role.role_id = infinitystone_role.id' + \
                ' LEFT JOIN infinitystone_tenant ON' + \
                ' infinitystone_user_role.tenant_id = infinitystone_tenant.id' + \
                ' OR infinitystone_user_role.tenant_id is NULL' + \
                ' where infinitystone_user_role.user_id = %s'
        if domain is not None:
            query += ' and infinitystone_user_role.domain = %s'
            values.append(domain)
        else:
            query += ' and infinitystone_user_role.domain IS NULL'

        if tenant_id is not None:
            query += ' and infinitystone_user_role.tenant_id = %s'
            values.append(tenant_id)
        else:
            query += ' and infinitystone_user_role.tenant_id IS NULL'

        crsr = conn.execute(query, values)

        for role in crsr:
            roles.append(role['role'])

    return roles


def authorize(tag, username=None, password=None, domain=None):
    with db() as conn:
        values = [tag, username, ]
        sql = 'SELECT username, password FROM infinitystone_user'
        sql += ' WHERE'
        sql += ' tag = %s'
        sql += ' AND username = %s'
        if domain is not None:
            sql += ' AND domain = %s'
            values.append(domain)
        else:
            sql += ' AND domain IS NULL'

        crsr = conn.execute(sql, values)
        result = crsr.fetchone()
        if result is not None:
            # Validate Password againts stored HASHED Value.
            if is_valid_password(password, result['password']):
                return True

        raise AccessDeniedError('Invalid credentials provided')

def tenants(req, domain=None, tenant_id=None):
        table = (" infinitystone_tenant" +
                 " LEFT JOIN" +
                 " infinitystone_user_role ON" +
                 " (infinitystone_user_role.tenant_id =" +
                 " infinitystone_tenant.id and" +
                 " infinitystone_user_role.domain =" +
                 " infinitystone_tenant.domain)" +

                 " or (infinitystone_user_role.tenant_id =" +
                 " infinitystone_tenant.tenant_id and" +
                 " infinitystone_user_role.domain =" +
                 " infinitystone_tenant.domain)" +

                 " or (infinitystone_user_role.tenant_id" +
                 " is null and infinitystone_user_role.domain =" +
                 " infinitystone_tenant.domain)" +
                 " or (infinitystone_user_role.tenant_id" +
                 " is null and" +
                 " infinitystone_user_role.domain is null)" +
                 " or (infinitystone_user_role.domain is null and" +
                 " infinitystone_user_role.tenant_id =" +
                 " infinitystone_tenant.id)")

        if not domain:
            # FOR WEB UI Role Assignments....
            # We need to get global only tenants in the domain..
            if tenant_id is None and req.credentials.tenant_id:
                return sql_list(req, 'infinitystone_tenant', ('id', 'name', 'crm_id',))
        where={"infinitystone_user_role.user_id": req.credentials.user_id}
        if tenant_id is not None:
            where["infinitystone_user_role.tenant_id"] = tenant_id

        if domain:
            # FOR WEB UI Role Assignments....
            # We need to get global only tenants..
            if domain == 'None':
                domain = None
            where['infinitystone_tenant.domain'] = domain
        elif req.credentials.domain:
            where['infinitystone_tenant.domain'] = req.credentials.domain

        return sql_list(req, table, (('infinitystone_tenant.id', 'id',),
                                     ('infinitystone_tenant.name', 'name',),
                                     ('infinitystone_tenant.crm_id', 'crm_id',),
                                     ('infinitystone_tenant.domain', 'domain',)),
                        group_by='infinitystone_tenant.id', where=where)                      


def domains(req):
    where={"infinitystone_user_role.user_id": req.credentials.user_id}
    table = (" infinitystone_domain" +
	     " LEFT JOIN" +
	     " infinitystone_user_role ON" +
	     " (infinitystone_user_role.domain =" +
	     " infinitystone_domain.name)" +
	     " or (infinitystone_user_role.domain" +
	     " is null and infinitystone_user_role.tenant_id" +
	     " is null)")

    return sql_list(req, table, (('infinitystone_domain.id', 'id',),
				 ('infinitystone_domain.name', 'name',),),
		    group_by='infinitystone_domain.name',
		    where=where)
