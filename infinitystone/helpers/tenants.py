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
