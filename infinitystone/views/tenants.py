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
from luxon.helpers.api import sql_list, obj
from luxon.utils import sql

from infinitystone.models.tenants import infinitystone_tenant


@register.resources()
class Tenants(object):
    def __init__(self):
        router.add('GET', '/v1/tenant/{id}', self.tenant,
                   tag='login')
        router.add('GET', '/v1/tenants', self.tenants,
                   tag='login')
        router.add('GET', '/v1/tenants/{domain}', self.tenants,
                   tag='login')
        router.add('GET', '/v1/tenants/{domain}/{tenant_id}', self.tenants,
                   tag='login')
        router.add('POST', '/v1/tenant', self.create,
                   tag='tenants:admin')
        router.add(['PUT', 'PATCH'], '/v1/tenant/{id}', self.update,
                   tag='tenants:admin')
        router.add('DELETE', '/v1/tenant/{id}', self.delete,
                   tag='tenants:admin')

    def tenant(self, req, resp, id):
        return obj(req, infinitystone_tenant, sql_id=id)

    def tenants(self, req, resp, domain=None, tenant_id=None):
        f_id = sql.Field('infinitystone_tenant.id')
        f_name = sql.Field('infinitystone_tenant.name')
        f_crm_id = sql.Field('infinitystone_tenant.crm_id')
        f_tenants_domain = sql.Field('infinitystone_tenant.domain')
        f_roles_domain = sql.Field('infinitystone_user_role.domain')
        f_tenants_tenant_id = sql.Field('infinitystone_tenant.tenant_id')
        f_roles_tenant_id = sql.Field('infinitystone_user_role.tenant_id')
        f_user_id = sql.Field('infinitystone_user_role.user_id')

        v_null = sql.Value(None)
        v_user_id = sql.Value(req.credentials.user_id)

        if domain:
            v_domain = sql.Value(domain)
        else:
            v_domain = sql.Value(req.context_domain)

        if tenant_id:
            v_tenant_id = sql.Value(tenant_id)
        else:
            v_tenant_id = sql.Value(req.context_tenant_id)

        # Check if domain and tenant matches.
        jg_user_role_dom_ten = sql.Group(
            sql.And(f_roles_tenant_id == f_id,
                    f_roles_domain == f_tenants_domain)
        )
        # Check if domain and sub tenant matches.
        jg_user_role_dom_subten = sql.Group(
            sql.And(f_roles_tenant_id == f_tenants_tenant_id,
                    f_roles_domain == f_tenants_domain)
        )
        # Check if tenant is null and domain matches.
        jg_user_role_dom = sql.Group(
            sql.And(f_roles_tenant_id == v_null,
                    f_roles_domain == f_tenants_domain)
        )
        # Check if tnenat is null and domain is null
        jg_user_role_null = sql.Group(
            sql.And(f_roles_tenant_id == v_null,
                    f_roles_domain == v_null)
        )
        # Check if domain is null and tenant id matches.
        jg_user_role_ten = sql.Group(
            sql.And(f_roles_tenant_id == f_id,
                    f_roles_domain == v_null)
        )
        # Check if domain is null and sub tenant id matches.
        jg_user_role_subten = sql.Group(
            sql.And(f_roles_tenant_id == f_tenants_tenant_id,
                    f_roles_domain == v_null)
        )

        j_user_role = sql.Or(jg_user_role_dom_ten,
                             jg_user_role_dom_subten,
                             jg_user_role_dom,
                             jg_user_role_null,
                             jg_user_role_ten,
                             jg_user_role_subten)

        select = sql.Select('infinitystone_tenant', distinct=True)
        select.fields = (f_id,
                         f_name,
                         f_crm_id,
                         f_tenants_domain,
                         f_tenants_tenant_id,)
        select.inner_join('infinitystone_user_role', j_user_role)
        select.where = f_user_id == v_user_id

        if domain and domain.lower() == 'none':
            select.where = f_tenants_domain == v_null
        else:
            select.where = f_tenants_domain == v_domain

        select.where = sql.Group(
            sql.Or(f_id == v_tenant_id,
                   f_tenants_tenant_id == v_tenant_id))

        return sql_list(req,
                        select,
                        context=False,
                        search={'infinitystone_tenant.name': str,
                                'infinitystone_tenant.crm_id': str,
                                'infinitystone_tenant.tenant_id': str})

    def create(self, req, resp):
        tenant = obj(req, infinitystone_tenant)
        tenant.commit()
        return tenant

    def update(self, req, resp, id):
        tenant = obj(req, infinitystone_tenant, sql_id=id)
        tenant.commit()
        return tenant

    def delete(self, req, resp, id):
        tenant = obj(req, infinitystone_tenant, sql_id=id)
        tenant.commit()
        return tenant
