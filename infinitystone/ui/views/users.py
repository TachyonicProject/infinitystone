# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Christiaan Frans Rademan.
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
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.bootstrap4 import form

from infinitystone.ui.models.users import infinitystone_user

g.nav_menu.add('/Accounts/Users',
               href='/accounts/users',
               tag='admin',
               feather='users')


@register.resources()
class Users():
    def __init__(self):
        router.add('GET',
                   '/accounts/users',
                   self.list,
                   tag='users:view')

        router.add('GET',
                   '/accounts/users/{id}',
                   self.view,
                   tag='users:view')

        router.add('GET',
                   '/accounts/users/delete/{id}',
                   self.delete,
                   tag='users:admin')

        router.add(('GET', 'POST',),
                   '/accounts/users/add',
                   self.add,
                   tag='users:admin')

        router.add(('GET', 'POST',),
                   '/accounts/users/edit/{id}',
                   self.edit,
                   tag='users:admin')

        router.add('POST', '/accounts/users/set_role/{user_id}',
                   self.set_role,
                   tag='users:admin')

        router.add('GET', '/accounts/users/rm_role/{user_id}/{role_id}',
                   self.rm_role,
                   tag='users:admin')

    def list(self, req, resp):
        return render_template('infinitystone.ui/users/list.html',
                               view='Users')

    def delete(self, req, resp, id):
        req.context.api.execute('DELETE', '/v1/user/%s' % id,
                                endpoint='identity')

    def view(self, req, resp, id):
        user = req.context.api.execute('GET', '/v1/user/%s' % id,
                                       endpoint='identity')
        html_form = form(infinitystone_user, user.json, readonly=True)
        return render_template('infinitystone.ui/users/view.html',
                               form=html_form,
                               id=id,
                               view="View User")

    def edit(self, req, resp, id):
        if req.method == 'POST':
            data = req.form_dict
            req.context.api.execute('PUT', '/v1/user/%s' % id,
                                    data=data,
                                    endpoint='identity')
            req.method = 'GET'
            return self.edit(req, resp, id)
        else:
            user = req.context.api.execute('GET', '/v1/user/%s' % id,
                                           endpoint='identity')
            html_form = form(infinitystone_user, user.json)
            return render_template('infinitystone.ui/users/edit.html',
                                   form=html_form,
                                   id=id,
                                   view="Edit User")

    def add(self, req, resp):
        if req.method == 'POST':
            data = req.form_dict
            response = req.context.api.execute('POST', '/v1/user',
                                               data=data,
                                               endpoint='identity')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(infinitystone_user)
            return render_template('infinitystone.ui/users/add.html',
                                   view='Add User',
                                   form=html_form)

    def set_role(self, req, resp, user_id):
        data = req.form_dict
        role = data.get('role')
        domain = data.get('domain')
        tenant_id = data.get('tenant_id')

        uri = '/v1/user_roles/%s/%s' % (user_id, role,)

        if domain:
            uri += '/%s' % domain

            if tenant_id:
                uri += '/%s' % tenant_id

        req.context.api.execute('POST', uri)

    def rm_role(self, req, resp, user_id, role_id):
        uri = '/v1/user_roles/%s/%s' % (user_id, role_id,)
        req.context.api.execute('DELETE', uri, endpoint='identity')
