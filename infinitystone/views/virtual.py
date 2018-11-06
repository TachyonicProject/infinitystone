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
from luxon import db
from luxon.utils.sql import build_where
from luxon.helpers.access import validate_access
from luxon.helpers.api import raw_list, sql_list, obj
from luxon.exceptions import DuplicateError, AccessDeniedError

from infinitystone.models.virtual import infinitystone_virtual
from infinitystone.models.nas import infinitystone_nas

from luxon import GetLogger

log = GetLogger(__name__)

@register.resources()
class Virtual(object):
    def __init__(self):
        # Normal Tachyonic uers.
        router.add('GET', '/v1/virtual/{id}', self.virtual,
                   tag='infrastructure:admin')
        router.add('GET', '/v1/virtual', self.virtuals,
                   tag='infrastructure:admin')
        router.add('POST', '/v1/virtual', self.create,
                   tag='infrastructure:admin')
        router.add(['PUT', 'PATCH'], '/v1/virtual/{id}', self.update,
                   tag='infrastructure:admin')
        router.add('DELETE', '/v1/virtual/{id}', self.delete,
                   tag='infrastructure:admin')

        router.add('GET', '/v1/virtual/{id}/nas', self.nas,
                   tag='infrastructure:admin')
        router.add('POST', '/v1/virtual/{id}/nas', self.add_nas,
                   tag='infrastructure:admin')
        router.add('DELETE', '/v1/virtual/{id}/nas', self.rm_nas,
                   tag='infrastructure:admin')

    def virtual(self, req, resp, id):
        return obj(req, infinitystone_virtual, sql_id=id,
                   hide=('password',))

    def virtuals(self, req, resp):
        return sql_list(req, 'infinitystone_virtual',
                        ('id', 'domain', 'name',))

    def create(self, req, resp):
        virtual = obj(req, infinitystone_virtual)
        virtual.commit()
        return virtual

    def update(self, req, resp, id):
        virtual = obj(req, infinitystone_virtual, sql_id=id)
        virtual.commit()
        return virtual

    def delete(self, req, resp, id):
        virtual = obj(req, infinitystone_virtual, sql_id=id)
        virtual.commit()

    def nas(self, req, resp, id):
        where = { 'virtual_id': id} 
        return sql_list(req, 'infinitystone_nas',
                        ('id', 'name', 'server', 'nas_type', 'secret'), where=where)
        

    def add_nas(self, req, resp, id):
        virtual = obj(req, infinitystone_nas)
        virtual['virtual_id'] = id
        virtual.commit()
        return virtual

    def rm_nas(self, req, resp, id):
        virtual = obj(req, infinitystone_nas, sql_id=id)
        virtual.commit()

