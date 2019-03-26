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
from luxon import db
from luxon.exceptions import HTTPForbidden
from luxon.utils.password import valid as is_valid_password
from luxon.exceptions import AccessDeniedError
from infinitystone.models.users import infinitystone_user


def user_tenant(user_id, role):
    tenants = []

    with db() as conn:
        query = "SELECT" + \
                " infinitystone_user_role.tenant_id as tenant_id" + \
                " FROM" + \
                " infinitystone_user_role LEFT JOIN infinitystone_role ON" + \
                " infinitystone_user_role.role_id = infinitystone_role.id" + \
                " WHERE infinitystone_user_role.user_id = %s" + \
                " AND infinitystone_role.name = %s" + \
                " AND infinitystone_user_role.tenant_id is not NULL"
        result = conn.execute(query, (user_id, role,)).fetchall()

    for tenant in result:
        tenants.append(tenant['tenant_id'])

    return tenants


def localize(username, domain, region=None, confederation=None, user_id=None):
    with db() as conn:
        values = [username, ]
        sql = 'SELECT * FROM infinitystone_user'
        sql += ' WHERE'
        sql += ' username = %s'
        if domain is not None:
            sql += ' AND domain = %s'
            values.append(domain)
        else:
            sql += ' AND domain IS NULL'
        result = conn.execute(sql,
                              values).fetchone()

        if result:
            if (result['roaming'] == 1):
                if (result['region'] and region and
                        result['region'] != region):
                    raise HTTPForbidden('Username exists in context already.')
                if (result['confederation'] and confederation and
                        result['confederation'] != confederation):
                    raise HTTPForbidden('Username exists in context already.')
            else:
                local_region = g.app.config.get(
                                'auth',
                                'region',
                                fallback='Region1'),
                local_confed = g.app.config.get(
                                'auth',
                                'confederation',
                                fallback='Confederation1')
                if ((region and region != local_region) or
                        (confederation and
                         confederation != local_confed)):
                    if (user_id != result['id']):
                        raise HTTPForbidden(
                            'Local username exists for roaming user.')
        elif not result:
            user_obj = infinitystone_user()
            user_obj['username'] = username
            if domain:
                user_obj['domain'] = domain
            if region:
                user_obj['region'] = region
            if confederation:
                user_obj['confederation'] = confederation
            user_obj['roaming'] = True

            user_obj.commit()


def authorize(username=None, password=None, domain=None):
    with db() as conn:
        values = [username, ]
        sql = 'SELECT username, password FROM infinitystone_user'
        sql += ' WHERE'
        sql += ' username = %s AND enabled = 1'
        sql += ' AND roaming = 0'
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
