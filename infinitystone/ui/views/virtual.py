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

from infinitystone.ui.models.virtual import infinitystone_virtual

g.nav_menu.add('/Infrastructure/Authentication/Virtual',
               href='/infrastructure/authentication/virtual',
               tag='infrastructure:admin',
               feather='at-sign')


@register.resources()
class Virtual():
    def __init__(self):
        router.add('GET',
                   '/infrastructure/authentication/virtual',
                   self.list,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/authentication/virtual/{id}',
                   self.view,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/authentication/virtual/delete/{id}',
                   self.delete,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/authentication/virtual/add',
                   self.add,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/authentication/virtual/edit/{id}',
                   self.edit,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/authentication/virtual/add_nas/{id}',
                   self.add_nas,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/authentication/virtual/rm_nas/{id}',
                   self.rm_nas,
                   tag='infrastructure:admin')

    def list(self, req, resp):
        return render_template('infinitystone.ui/virtual/list.html',
                               view='Virtual Authentication Sevices')

    def delete(self, req, resp, id):
        req.context.api.execute('DELETE', '/v1/virtual/%s' % id,
                                endpoint='identity')

    def view(self, req, resp, id):
        vr = req.context.api.execute('GET', '/v1/virtual/%s' % id,
                                     endpoint='identity')
        html_form = form(infinitystone_virtual, vr.json, readonly=True)
        return render_template('infinitystone.ui/virtual/view.html',
                               view='View Virtual Authentication Service',
                               form=html_form,
                               id=id)

    def edit(self, req, resp, id):
        if req.method == 'POST':
            req.context.api.execute('PUT', '/v1/virtual/%s' % id,
                                    data=req.form_dict,
                                    endpoint='identity')
            return self.view(req, resp, id)
        else:
            domain = req.context.api.execute('GET', '/v1/virtual/%s' % id,
                                             endpoint='identity')
            html_form = form(infinitystone_virtual, domain.json)
            return render_template('infinitystone.ui/virtual/edit.html',
                                   view='Edit Virtual Authentication Service',
                                   form=html_form,
                                   id=id)

    def add(self, req, resp):
        if req.method == 'POST':
            response = req.context.api.execute('POST', '/v1/virtual',
                                               data=req.form_dict,
                                               endpoint='identity')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(infinitystone_virtual)
            return render_template('infinitystone.ui/virtual/add.html',
                                   view='Add Virtual Authentication Service',
                                   form=html_form)

    def add_nas(self, req, resp, id):
        data = req.form_dict

        uri = '/v1/virtual/%s/nas' % id

        response = req.context.api.execute('POST', uri, data=data,
                                           endpoint='identity')

    def rm_nas(self, req, resp, id):
        uri = '/v1/virtual/%s/nas' % id
        response = req.context.api.execute('DELETE', uri, endpoint='identity')  
