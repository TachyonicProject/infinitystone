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
from luxon import register
from luxon import router
from luxon import GetLogger
from luxon.helpers.api import sql_list, obj
from infinitystone.models.domains import infinitystone_domain
from luxon.utils import sql

log = GetLogger(__name__)


@register.resources()
class Domains(object):
    def __init__(self):
        router.add('GET', '/v1/domain/{id}', self.domain,
                   tag='login')
        router.add('GET', '/v1/domains', self.domains,
                   tag='login')
        router.add('POST', '/v1/domain', self.create,
                   tag='domains:admin')
        router.add(['PUT', 'PATCH'], '/v1/domain/{id}', self.update,
                   tag='domains:admin')
        router.add('DELETE', '/v1/domain/{id}', self.delete,
                   tag='domains:admin')

    def domain(self, req, resp, id):
        return obj(req, infinitystone_domain, sql_id=id)

    def domains(self, req, resp):
        f_domain_id = sql.Field('infinitystone_domain.id')
        f_name = sql.Field('infinitystone_domain.name')
        f_domain = sql.Field('infinitystone_user_role.domain')
        f_tenant_id = sql.Field('infinitystone_user_role.tenant_id')
        f_user_id = sql.Field('infinitystone_user_role.user_id')
        j_user_role = sql.Or(
            sql.Group(f_domain == f_name),
            sql.Group(sql.And(f_domain == sql.Value(None),
                              f_tenant_id == sql.Value(None))))
        w_user_id = f_user_id == sql.Value(req.credentials.user_id)
        select = sql.Select('infinitystone_domain',
                            distinct=True)
        select.fields = f_domain_id, f_name
        select.inner_join('infinitystone_user_role', j_user_role)
        select.where = w_user_id

        return sql_list(req,
                        select,
                        context=False,
                        search={'name': str})

    def create(self, req, resp):
        domain = obj(req, infinitystone_domain)
        domain.commit()
        return domain

    def update(self, req, resp, id):
        domain = obj(req, infinitystone_domain, sql_id=id)
        domain.commit()
        return domain

    def delete(self, req, resp, id):
        domain = obj(req, infinitystone_domain, sql_id=id)
        domain.commit()
        return domain
