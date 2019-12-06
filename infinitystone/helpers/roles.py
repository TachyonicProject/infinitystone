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
