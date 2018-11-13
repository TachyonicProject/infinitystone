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
from luxon.utils.sql import build_where, build_like


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
