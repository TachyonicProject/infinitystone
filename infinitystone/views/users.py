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
from luxon.utils.password import hash
from psychokinetic.utils.api import sql_list, obj

from infinitystone.models.users import infinitystone_user


@register.resources()
class Users(object):
    def __init__(self):
        router.add('GET', '/v1/user/{id}', self.user,
                   tag='users:view')
        router.add('GET', '/v1/users', self.users,
                   tag='users:view')
        router.add('POST', '/v1/user', self.create,
                   tag='users:admin')
        router.add(['PUT', 'PATCH'], '/v1/user/{id}', self.update,
                   tag='users:admin')
        router.add('DELETE', '/v1/user/{id}', self.delete,
                   tag='users:admin')

    def user(self, req, resp, id):
        return obj(req, infinitystone_user, sql_id=id, hide=('password',))

    def users(self, req, resp):
        return sql_list(req, 'infinitystone_user', ('id', 'username', 'name'))

    def create(self, req, resp):
        user = obj(req, infinitystone_user, hide=('password',))
        if req.json.get('password') is not None:
            user['password'] = hash(req.json['password'])
        user.commit()
        return user

    def update(self, req, resp, id):
        user = obj(req, infinitystone_user, sql_id=id, hide=('password',))
        if req.json.get('password') is not None:
            user['password'] = hash(req.json['password'])
        user.commit()
        return user

    def delete(self, req, resp, id):
        user = obj(req, infinitystone_user, sql_id=id, hide=('password',))
        user.commit()
        return user
