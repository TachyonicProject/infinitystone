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

from luxon import db
from luxon.utils.sql import build_where, build_like
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
        roles = crsr.fetchall()
        return roles


def get_context_roles(user_id, domain=None, tenant_id=None):
    roles = []
    with db() as conn:
        values = []
        values.append(user_id)
        query = 'SELECT' + \
                ' infinitystone_role.name as role' + \
                ' FROM' + \
                ' infinitystone_user_role LEFT JOIN infinitystone_role ON' + \
                ' infinitystone_user_role.role_id = infinitystone_role.id' + \
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

def get_tenants(user_id=None, domain=None, tenant_id=None,
                page=1, limit=10, search=None):
    start = (page - 1) * limit
    sql = "SELECT DISTINCT"
    sql += " infinitystone_tenant.id as id,"
    sql += " infinitystone_tenant.name as name,"
    sql += " infinitystone_tenant.crm_id as crm_id,"
    sql += " infinitystone_tenant.domain as domain"
    sql += " FROM infinitystone_tenant"
    sql += " INNER JOIN infinitystone_user_role"
    sql += " ON"
    # Check if domain and tenant matches.
    sql += " (infinitystone_user_role.tenant_id ="
    sql += " infinitystone_tenant.id"
    sql += " AND infinitystone_user_role.domain ="
    sql += " infinitystone_tenant.domain)"
    # Check if domain and sub tenant matches.
    sql += " OR (infinitystone_user_role.tenant_id ="
    sql += " infinitystone_tenant.tenant_id"
    sql += " AND infinitystone_user_role.domain ="
    sql += " infinitystone_tenant.domain)"
    # Check if tenant is null and domain matches.
    sql += " OR (infinitystone_user_role.tenant_id is null"
    sql += " AND infinitystone_user_role.domain ="
    sql += " infinitystone_tenant.domain)"
    # Check if tnenat is null and domain is null
    sql += " OR (infinitystone_user_role.tenant_id is null"
    sql += " AND infinitystone_user_role.domain is null)"
    # Check if domain is null and tenant id matches.
    sql += " OR (infinitystone_user_role.domain is null"
    sql += " AND infinitystone_user_role.tenant_id ="
    sql += " infinitystone_tenant.id)"
    # Check if domain is null and sub tenant id matches.
    sql += " OR (infinitystone_user_role.domain is null"
    sql += " AND infinitystone_user_role.tenant_id ="
    sql += " infinitystone_tenant.tenant_id)"

    where = {}
    where2 = {}
    like = {}
    if user_id:
        where['infinitystone_user_role.user_id'] = user_id
    if domain:
        where['infinitystone_tenant.domain'] = domain
    if tenant_id:
        where2 = {}
        where2['infinitystone_tenant.tenant_id'] = tenant_id
        where2['infinitystone_tenant.id'] = tenant_id

    where, values = build_where(**where)
    where2, values2 = build_where('OR', **where2)
    if values2:
        where += " AND " + where2
        values += values2

    if search:
        where3, values3 = build_like('OR', **search)
        if values3:
            where += " AND " + where3
            values += values3

    with db() as conn:
        if values:
            return conn.execute(sql + 'WHERE ' + where +
                                ' LIMIT %s, %s' % (start, limit,),
                                values).fetchall()
        else:
            return conn.execute(sql +
                                ' LIMIT %s, %s' % (start, limit,),
                                values).fetchall()
        

def get_domains(user_id, page=1, limit=10, search=None):
    start = (page - 1) * limit

    sql = "SELECT DISTINCT infinitystone_domain.id AS id"
    sql += " ,infinitystone_domain.name AS name"
    sql += " FROM infinitystone_domain"
    sql += " INNER JOIN infinitystone_user_role"
    sql += " ON (infinitystone_user_role.domain ="
    sql += " infinitystone_domain.name)"
    sql += " OR (infinitystone_user_role.domain IS null"
    sql += " and infinitystone_user_role.tenant_id IS null)"
    where={"infinitystone_user_role.user_id": user_id}

    where, values = build_where(**where)
    if search:
        where2, values2 = build_like('OR', **search)
        if values2:
            where += " AND " + where2
            values += values2

    with db() as conn:
        return conn.execute(sql + 'WHERE ' + where +
                            ' LIMIT %s, %s' % (start, limit,),
                            values).fetchall()
