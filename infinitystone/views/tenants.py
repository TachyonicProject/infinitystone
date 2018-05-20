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
from psychokinetic.utils.api import sql_list, obj

from infinitystone.models.tenants import luxon_tenant


@register.resources()
class Tenants(object):
    def __init__(self):
        router.add('GET', '/v1/tenant/{id}', self.tenant,
                   tag='tenants:view')
        router.add('GET', '/v1/tenants', self.tenants,
                   tag='tenants:view')
        router.add('POST', '/v1/tenant', self.create,
                   tag='tenants:admin')
        router.add(['PUT', 'PATCH'], '/v1/tenant/{id}', self.update,
                   tag='tenants:admin')
        router.add('DELETE', '/v1/tenant/{id}', self.delete,
                   tag='tenants:admin')

    def tenant(self, req, resp, id):
        return obj(req, luxon_tenant, sql_id=id)

    def tenants(self, req, resp):
        return sql_list(req, 'luxon_tenant', ('id',))

    def create(self, req, resp):
        tenant = obj(req, luxon_tenant)
        tenant.commit()
        return tenant

    def update(self, req, resp, id):
        tenant = obj(req, luxon_tenant, sql_id=id)
        tenant.commit()
        return tenant

    def delete(self, req, resp, id):
        tenant = obj(req, luxon_tenant, sql_id=id)
        tenant.commit()
        return tenant
