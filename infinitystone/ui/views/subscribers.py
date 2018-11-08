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
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.bootstrap4 import form
from luxon.utils.html5 import select

from infinitystone.ui.models.subscribers import infinitystone_subscriber

g.nav_menu.add('/Accounts/Subscribers',
               href='/accounts/subscribers',
               tag='services:view',
               feather='users')


@register.resources()
class Subscribers():
    def __init__(self):
        router.add('GET',
                   '/accounts/subscribers',
                   self.list,
                   tag='services:view')

        router.add('GET',
                   '/accounts/subscribers/{id}',
                   self.view,
                   tag='services:view')

        router.add('GET',
                   '/accounts/subscribers/delete/{id}',
                   self.delete,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/accounts/subscribers/add',
                   self.add,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/accounts/subscribers/edit/{id}',
                   self.edit,
                   tag='services:admin')

        router.add('POST', '/accounts/subscribers/add_attr/{user_id}',
                   self.add_attr,
                   tag='services:admin')

        router.add('GET', '/accounts/subscribers/rm_attr/{user_id}/{attribute_id}',
                   self.rm_attr,
                   tag='services:admin')

        router.add('POST', '/accounts/subscribers/add_group/{user_id}',
                   self.add_group,
                   tag='services:admin')

        router.add('GET', '/accounts/subscribers/rm_group/{user_id}/{group_id}',
                   self.rm_group,                                                   
                   tag='services:admin')

    def list(self, req, resp):
        return render_template('infinitystone.ui/subscribers/list.html',
                               view='Subscribers')

    def delete(self, req, resp, id):
        req.context.api.execute('DELETE', '/v1/user/%s/radius' % id,
                                endpoint='identity')

    def view(self, req, resp, id):
        user = req.context.api.execute('GET', '/v1/user/%s/radius' % id,
                                       endpoint='identity')
        html_form = form(infinitystone_subscriber, user.json, readonly=True)
        return render_template('infinitystone.ui/subscribers/view.html',
                               form=html_form,
                               id=id,
                               view="View Subscriber")

    def edit(self, req, resp, id):
        if req.method == 'POST':
            data = req.form_dict
            req.context.api.execute('PUT', '/v1/user/%s/radius' % id,
                                    data=data,
                                    endpoint='identity')
            req.method = 'GET'
            return self.edit(req, resp, id)
        else:
            user = req.context.api.execute('GET', '/v1/user/%s/radius' % id,
                                           endpoint='identity')
            html_form = form(infinitystone_subscriber, user.json)
            return render_template('infinitystone.ui/subscribers/edit.html',
                                   form=html_form,
                                   id=id,
                                   view="Edit Subscriber")

    def add(self, req, resp):
        if req.method == 'POST':
            data = req.form_dict
            response = req.context.api.execute('POST', '/v1/user/radius',
                                               data=data,
                                               endpoint='identity')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(infinitystone_subscriber)
            return render_template('infinitystone.ui/subscribers/add.html',
                                   view='Add Subscriber',
                                   form=html_form)

    def add_group(self, req, resp, user_id):
        uri = '/v1/user_group/%s' % user_id
        response = req.context.api.execute('POST', uri, data=req.form_dict)

    def rm_group(self, req, resp, user_id, group_id):
        uri = '/v1/user_group/%s/%s' % (user_id, group_id,)
        response = req.context.api.execute('DELETE', uri, endpoint='identity')

    def add_attr(self, req, resp, user_id):
        uri = '/v1/user_attr/%s' % user_id
        response = req.context.api.execute('POST', uri, data=req.form_dict)

    def rm_attr(self, req, resp, user_id, attribute_id):
        uri = '/v1/user_attr/%s/%s' % (user_id, attribute_id,)
        response = req.context.api.execute('DELETE', uri, endpoint='identity') 
