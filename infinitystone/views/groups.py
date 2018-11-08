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

from infinitystone.models.groups import infinitystone_group
from infinitystone.models.group_attrs import infinitystone_group_attr


@register.resources()
class Groups(object):
    def __init__(self):
        router.add('GET', '/v1/group/{id}', self.group,
                   tag='services')
        router.add('GET', '/v1/groups', self.groups,
                   tag='services')
        router.add('POST', '/v1/group', self.create,
                   tag='services')
        router.add(['PUT', 'PATCH'], '/v1/group/{id}', self.update,
                   tag='services')
        router.add('DELETE', '/v1/group/{id}', self.delete,
                   tag='services')
        router.add('GET', '/v1/group/{id}/attrs', self.attrs,
                   tag='services')
        router.add('POST', '/v1/group/{id}/attrs', self.add_attr,
                   tag='services')
        router.add('DELETE', '/v1/group/{id}/attrs', self.rm_attr,
                   tag='services')

    def group(self, req, resp, id):
        return obj(req, infinitystone_group, sql_id=id)

    def groups(self, req, resp):
        return sql_list(req, 'infinitystone_group', ('id', 'name', ))

    def create(self, req, resp):
        group = obj(req, infinitystone_group)
        group.commit()
        return group

    def update(self, req, resp, id):
        group = obj(req, infinitystone_group, sql_id=id)
        group.commit()
        return group

    def delete(self, req, resp, id):
        group = obj(req, infinitystone_group, sql_id=id)
        group.commit()
        return group

    def attrs(self, req, resp, id):
        where = { 'group_id': id }
        return sql_list(req, 'infinitystone_group_attr',
                        ('id', 'attribute', 'op', 'value', 'ctx', ),
                        where=where)
       
    def add_attr(self, req, resp, id):
        attr = obj(req, infinitystone_group_attr)
        attr['group_id'] = id
        attr.commit()
        return attr

    def rm_attr(self, req, resp, id):
        attr = obj(req, infinitystone_group_attr, sql_id=id)
        attr.commit()
