# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Dave Kruger, Christiaan Rademan.
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
from luxon.utils.pkg import EntryPoints
from luxon.exceptions import FieldMissing

from infinitystone.ui.models.elements import infinitystone_element

g.nav_menu.add('/Infrastructure/Elements',
               href='/infrastructure/elements',
               tag='services',
               endpoint='identity',
               feather='server')


def render_model(element_model, eid, mval, mtype, view, data=None,
                 ro=False, **kwargs):
    html_form = form(element_model, data, readonly=ro)
    return render_template('infinitystone.ui/elements/%s.html' % mtype,
                           view='%s %s %s' % (view, mval, mtype),
                           form=html_form,
                           id=eid,
                           model=mval,
                           **kwargs)


@register.resources()
class Elements:
    def __init__(self):
        router.add('GET',
                   '/infrastructure/elements',
                   self.list,
                   tag='infrastructure:view')

        router.add('GET',
                   '/infrastructure/elements/{eid}',
                   self.view,
                   tag='infrastructure:view')

        router.add('GET',
                   '/infrastructure/elements/delete/{eid}',
                   self.delete,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/elements/add',
                   self.add,
                   tag='infrastructure:admin')

        router.add(('POST', 'GET',),
                   '/infrastructure/elements/edit/{eid}',
                   self.edit,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/elements/{eid}/interface',
                   self.interface,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/interfaces/{eid}/{interface}',
                   self.add_interface,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/interfaces/edit/{eid}/{interface}',
                   self.update_interface,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/interfaces/edit/{eid}/{interface}',
                   self.edit_interface,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/interfaces/delete/{eid}/{interface}',
                   self.delete_interface,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/interfaces/{eid}/{interface}',
                   self.view_interface,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/elements/{eid}/attributes',
                   self.attributes,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/elements/{eid}/{classification}',
                   self.add_attributes,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/elements/edit/{eid}/{classification}',
                   self.update_attributes,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/elements/edit/{eid}/{classification}',
                   self.edit_attributes,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/elements/delete/{eid}/{classification}',
                   self.delete_attributes,
                   tag='infrastructure:admin')

    def list(self, req, resp):
        return render_template('infinitystone.ui/elements/list.html',
                               view='Elements')

    def delete(self, req, resp, eid):
        req.context.api.execute('DELETE', '/v1/element/%s' % eid,
                                endpoint='identity')

    def view(self, req, resp, eid):
        element = req.context.api.execute('GET', '/v1/element/%s' % eid,
                                          endpoint='identity')
        attrs = {}

        for a in element.json['classifications']:
            classification = EntryPoints('tachyonic.element.classifications')[
                a['classification']]
            attrs[a['classification']] = form(classification,
                                              a['metadata'],
                                              readonly=True)

        parent_name = None

        if 'parent' in element.json:
            parent_name = element.json['parent']['name']

        html_form = form(infinitystone_element, element.json, readonly=True)
        return render_template('infinitystone.ui/elements/view.html',
                               view='View Element',
                               form=html_form,
                               id=eid,
                               attrs=attrs,
                               parent=parent_name)

    def edit(self, req, resp, eid):
        if req.method == 'POST':
            req.context.api.execute('PUT', '/v1/element/%s' % eid,
                                    data=req.form_dict,
                                    endpoint='identity')
            return self.view(req, resp, eid)
        else:

            element = req.context.api.execute('GET', '/v1/element/%s' % eid,
                                              endpoint='identity')

            parent_name = None

            if 'parent' in element.json:
                parent_name = element.json['parent']['name']

            html_form = form(infinitystone_element, element.json)
            return render_template('infinitystone.ui/elements/edit.html',
                                   view='Edit Element',
                                   name=element.json['name'],
                                   form=html_form,
                                   id=eid,
                                   parent=parent_name,
                                   parent_id=element.json['parent_id'])

    def add(self, req, resp):
        if req.method == 'POST':
            response = req.context.api.execute('POST', '/v1/element',
                                               data=req.form_dict,
                                               endpoint='identity')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(infinitystone_element)
            return render_template('infinitystone.ui/elements/add.html',
                                   view='Add Element',
                                   form=html_form)

    def interface(self, req, resp, eid):
        try:
            interface = req.form_dict['interface']
        except KeyError:
            raise FieldMissing('Interface', 'Element Interface',
                               'Please select Interface for Element')
        model = EntryPoints('tachyonic.element.interfaces')[interface].model

        return render_model(model, eid, interface, 'interface', view="Add")

    def add_interface(self, req, resp, eid, interface):
        req.context.api.execute('POST',
                                '/v1/element/%s/%s' % (eid, interface,),
                                data=req.form_dict,
                                endpoint='identity')
        req.method = 'GET'
        return self.edit(req, resp, eid)

    def update_interface(self, req, resp, eid, interface):
        req.context.api.execute('PUT', '/v1/element/%s/%s' % (eid, interface,),
                                data=req.form_dict,
                                endpoint='identity')
        req.method = 'GET'
        return self.view_interface(req, resp, eid, interface)

    def edit_interface(self, req, resp, eid, interface):
        e_int = req.context.api.execute('GET',
                                        '/v1/element/%s/%s' % (
                                            eid, interface,),
                                        data=req.form_dict,
                                        endpoint='identity')

        model = EntryPoints('tachyonic.element.interfaces')[interface].model

        return render_model(model, eid, interface,
                            'interface', view="Edit",
                            data=e_int.json['metadata'])

    def view_interface(self, req, resp, eid, interface):
        e_int = req.context.api.execute('GET',
                                        '/v1/element/%s/%s' % (
                                            eid, interface,),
                                        endpoint='identity')
        model = EntryPoints('tachyonic.element.interfaces')[interface].model

        return render_model(model, eid, interface,
                            'interface', view="View",
                            data=e_int.json['metadata'], ro=True)

    def delete_interface(self, req, resp, eid, interface):
        req.context.api.execute('DELETE',
                                '/v1/element/%s/%s' % (eid, interface,),
                                data=req.form_dict,
                                endpoint='identity')

    def attributes(self, req, resp, eid):
        try:
            classification = req.form_dict['classification']
        except KeyError:
            raise FieldMissing('classification', 'Element classification',
                               'Please select Cateopgry for Element')

        model = EntryPoints('tachyonic.element.classifications')[
            classification]

        return render_model(model, eid, classification,
                            'attributes', view="Add")

    def add_attributes(self, req, resp, eid, classification):
        req.context.api.execute('POST',
                                '/v1/element/%s/attributes/%s' % (
                                    eid, classification,),
                                data=req.form_dict,
                                endpoint='identity')

        req.method = 'GET'

        return self.edit(req, resp, eid)

    def update_attributes(self, req, resp, eid, classification):
        req.context.api.execute('PUT',
                                '/v1/element/%s/attributes/%s' % (
                                    eid, classification,),
                                data=req.form_dict,
                                endpoint='identity')
        req.method = 'GET'
        return self.edit(req, resp, eid)

    def edit_attributes(self, req, resp, eid, classification):
        e_attr = req.context.api.execute('GET',
                                         '/v1/element/%s/attributes/%s' % (
                                            eid, classification,),
                                         endpoint='identity').json
        model = EntryPoints('tachyonic.element.classifications')[
            classification]

        return render_model(model, eid, e_attr['classification'], 'attributes',
                            view="Edit", data=e_attr['metadata'],
                            aid=e_attr['id'])

    def delete_attributes(self, req, resp, eid, classification):
        req.context.api.execute('DELETE',
                                '/v1/element/%s/attributes/%s' % (
                                    eid, classification,),
                                data=req.form_dict)

        element = req.context.api.execute('GET', '/v1/element/%s' % eid,
                                          endpoint='identity')

        parent_name = None

        if 'parent' in element.json:
            parent_name = element.json['parent']['name']

        html_form = form(infinitystone_element, element.json)
        return render_template('infinitystone.ui/elements/edit.html',
                               view='Edit Element',
                               form=html_form,
                               id=eid,
                               parent=parent_name,
                               parent_id=element.json['parent_id'])

        return self.edit(req, resp, eid)
