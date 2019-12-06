# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Christiaan Frans Rademan <chris@fwiw.co.za>.
# Copyright (c) 2018-2019 David Kruger.
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
from uuid import uuid4

from luxon import register
from luxon import router
from luxon import db
from luxon.utils import js
from luxon.utils.pkg import EntryPoints
from luxon.exceptions import NotFoundError
from luxon.exceptions import SQLOperationalError
from luxon.exceptions import SQLProgrammingError
from luxon.helpers.api import raw_list, sql_list, obj
from luxon.helpers.access import validate_access
from luxon.utils.cast import to_list

from infinitystone.models.elements import infinitystone_element
from infinitystone.models.elements import infinitystone_element_interface
from infinitystone.models.elements import infinitystone_element_classifications

from luxon.helpers.crypto import Crypto


def get_related(eid, table, where):
    if eid is None:
        return []

    sql = "SELECT * FROM %s WHERE %s=?" % (table, where,)

    with db() as conn:
        crsr = conn.execute(sql, eid)
        related = to_list(crsr.fetchall())

    return related


def get_element_interface(eid, interface):
    with db() as conn:
        cursor = conn.execute('SELECT interface, metadata, creation_time' +
                              ' FROM infinitystone_element_interface' +
                              ' WHERE element_id = %s' +
                              ' AND interface = %s', (eid, interface,))
        interface = cursor.fetchone()

        if interface is None:
            raise NotFoundError('Interface not found')

        crypto = Crypto()
        interface_metadata = crypto.decrypt(interface['metadata'])
        interface['metadata'] = js.loads(interface_metadata)

        return interface


@register.resources()
class Elements(object):
    def __init__(self):
        router.add('GET', '/v1/elements',
                   self.list_elements,
                   tag='infrastructure:view')

        router.add('GET', '/v1/elements/parents',
                   self.list_parents,
                   tag='infrastructure:view')

        router.add('GET', '/v1/element/{eid}',
                   self.view_element,
                   tag='infrastructure:view')

        router.add('POST', '/v1/element',
                   self.add_element,
                   tag='infrastructure:admin')

        router.add('POST', '/v1/element/{eid}',
                   self.add_element,
                   tag='infrastructure:admin')

        router.add(['PUT', 'PATCH'], '/v1/element/{eid}',
                   self.update_element,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/element/{eid}',
                   self.delete_element,
                   tag='infrastructure:admin')

        router.add('POST', '/v1/element/{eid}/{interface}',
                   self.add_interface,
                   tag='infrastructure:admin')

        router.add(['PATCH', 'PUT'], '/v1/element/{eid}/{interface}',
                   self.update_interface,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/element/{eid}/{interface}',
                   self.delete_interface,
                   tag='infrastructure:admin')

        router.add('GET', '/v1/element/{eid}/{interface}',
                   self.view_interface,
                   tag='infrastructure:view')

        router.add('POST', '/v1/element/{eid}/tag/{tag}',
                   self.add_tag,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/element/{eid}/tag/{tag}',
                   self.delete_tag,
                   tag='infrastructure:admin')

        router.add('GET', '/v1/element/{eid}/attributes/{classification}',
                   self.view_attributes,
                   tag='infrastructure:view')

        router.add('POST', '/v1/element/{eid}/attributes/{classification}',
                   self.add_attributes,
                   tag='infrastructure:admin')

        router.add(['PATCH', 'PUT'],
                   '/v1/element/{eid}/attributes/{classification}',
                   self.update_attributes,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/element/{eid}/attributes/{classification}',
                   self.delete_attributes,
                   tag='infrastructure:admin')

    def list_elements(self, req, resp):
        return sql_list(req,
                        'infinitystone_element',
                        fields=('id',
                                'tenant_id',
                                'parent_id',
                                'name',
                                'enabled',
                                'creation_time',),
                        search={'id': str,
                                'tenant_id': str,
                                'parent_id': str,
                                'name': str})

    def list_parents(self, req, resp):
        sql = 'SELECT * FROM infinitystone_element'
        vals = []

        with db() as conn:
            elements = conn.execute(sql, vals).fetchall()

        return raw_list(req, elements, context=False)

    def add_element(self, req, resp, eid=None):
        element = obj(req, infinitystone_element)
        if eid is not None:
            element['parent_id'] = eid
        element.commit()
        return element

    def _get_children(self, req, eid):
        element = infinitystone_element()
        element.sql_id(eid)
        validate_access(req, element)

        children = []

        for child in get_related(eid, 'infinitystone_element', 'parent_id'):
            child = {"id": child['id'],
                     "child_name": child['name'],
                     "domain": child['domain'],
                     "tenant_id": child['tenant_id']}
            children.append(child)

        return children

    def _get_interfaces(self, req, eid):
        element = infinitystone_element()
        element.sql_id(eid)
        validate_access(req, element)

        interfaces = []

        for interface in get_related(eid, 'infinitystone_element_interface',
                                     'element_id'):
            interface = {"id": interface['interface'],
                         "interface": interface['interface'],
                         "metadata": interface['metadata']}
            interfaces.append(interface)

        return interfaces

    def _get_attributes(self, req, eid):
        element = infinitystone_element()
        element.sql_id(eid)
        validate_access(req, element)

        attributes = []

        for attrs in get_related(eid, 'infinitystone_element_classifications',
                                 'element_id'):
            attrs = {"id": attrs['id'],
                     "classification": attrs['classification'],
                     "metadata": js.loads(attrs['metadata'])}
            attributes.append(attrs)

        return attributes

    def view_element(self, req, resp, eid):
        view = req.query_params.get('view', False)
        if view:
            if view == 'children':
                children = self._get_children(req, eid)
                return raw_list(req, children, context=False)
            if view == 'interfaces':
                interfaces = self._get_interfaces(req, eid)
                return raw_list(req, interfaces, context=False)
            if view == 'attributes':
                attributes = self._get_attributes(req, eid)
                return raw_list(req, attributes, context=False)

        element = obj(req, infinitystone_element, sql_id=eid)

        to_return = element.dict

        with db() as conn:
            children = conn.execute("SELECT id, name, enabled, creation_time"
                                    " FROM infinitystone_element"
                                    " WHERE parent_id = %s", eid).fetchall()
            interfaces = conn.execute("SELECT interface,metadata,creation_time"
                                      " FROM infinitystone_element_interface"
                                      " WHERE element_id = %s", eid).fetchall()
            classifications = conn.execute(
                "SELECT classification,metadata,"
                " creation_time FROM"
                " infinitystone_element_classifications"
                " WHERE element_id = %s",
                eid).fetchall()
            tags = conn.execute("SELECT name"
                                " FROM infinitystone_element_tag"
                                " WHERE element_id = %s", eid).fetchall()
            try:
                parent = conn.execute("SELECT name FROM infinitystone_element "
                                      "WHERE id=%s",
                                      element['parent_id']).fetchone()
                to_return['parent'] = parent
            except (SQLOperationalError, SQLProgrammingError,):
                # when parent_id is None, sqlite raises Operational error,
                # whereas mysql raises Programming
                pass

        to_return['children'] = children
        to_return['interfaces'] = interfaces
        to_return['classifications'] = classifications
        to_return['tags'] = tags

        crypto = Crypto()
        for interfaces in to_return['interfaces']:
            interfaces_metadata = crypto.decrypt(interfaces['metadata'])
            interfaces['metadata'] = js.loads(interfaces_metadata)

        for attrs in to_return['classifications']:
            attrs['metadata'] = js.loads(attrs['metadata'])

        return to_return

    def update_element(self, req, resp, eid):
        element = obj(req, infinitystone_element, sql_id=eid)
        element.commit()
        return self.view_element(req, resp, eid)

    def delete_element(self, req, resp, eid):
        element = obj(req, infinitystone_element, sql_id=eid)
        element.commit()
        return element

    def add_interface(self, req, resp, eid, interface):
        metadata_model = EntryPoints('tachyonic.element.interfaces')[
            interface].model()
        metadata_model.update(req.json)
        # Check to see all required data was submittied
        metadata_model._pre_commit()
        metadata = metadata_model.json
        element = infinitystone_element()
        element.sql_id(eid)
        crypto = Crypto()
        metadata = crypto.encrypt(metadata)
        model = infinitystone_element_interface()
        model['element_id'] = eid
        model['interface'] = interface
        model['metadata'] = metadata
        model.commit()
        return self.view_interface(req, resp, eid, interface)

    def view_interface(self, req, resp, eid, interface):
        return get_element_interface(eid, interface)

    def update_interface(self, req, resp, eid, interface):
        # In case not all fields was submitted,
        # first we grab what we had.
        current = self.view_interface(req, resp, eid, interface)
        crypto = Crypto()
        model = EntryPoints('tachyonic.element.interfaces')[interface].model()
        model.update(current['metadata'])
        model.update(req.json)
        model_json = crypto.encrypt(model.json)
        with db() as conn:
            conn.execute('UPDATE infinitystone_element_interface' +
                         ' SET metadata = %s'
                         ' WHERE element_id = %s' +
                         ' AND interface = %s', (model_json,
                                                 eid, interface,))
            conn.commit()
        return self.view_interface(req, resp, eid, interface)

    def delete_interface(self, req, resp, eid, interface):
        with db() as conn:
            conn.execute('DELETE FROM infinitystone_element_interface' +
                         ' WHERE element_id = %s' +
                         ' AND interface = %s', (eid, interface,))
            conn.commit()

    def add_tag(self, req, resp, eid, tag):
        tag_entry_id = str(uuid4())
        with db() as conn:
            conn.execute('INSERT INTO infinitystone_element_tag' +
                         ' (id, name, element_id)' +
                         ' VALUES' +
                         ' (%s, %s, %s)', (tag_entry_id, tag, eid))
            conn.commit()
            return self.view_element(req, resp, eid)

    def delete_tag(self, req, resp, eid, tag):
        with db() as conn:
            conn.execute('DELETE FROM infinitystone_element_tag' +
                         ' WHERE element_id = %s' +
                         ' AND name = %s', (eid, tag,))
            conn.commit()
            return self.view_element(req, resp, eid)

    def view_attributes(self, req, resp, eid, classification):
        obj = infinitystone_element_classifications()
        obj.sql_id(classification)
        result = obj.dict
        result['metadata'] = js.loads(result['metadata'])
        return result

    def add_attributes(self, req, resp, eid, classification):
        metadata_model = EntryPoints('tachyonic.element.classifications')[
            classification]()
        metadata_model.update(req.json)
        # Check to see all required data was submittied
        metadata_model._pre_commit()
        metadata = metadata_model.json
        element = infinitystone_element()
        element.sql_id(eid)
        model = infinitystone_element_classifications()
        model['element_id'] = eid
        model['metadata'] = metadata
        model['classification'] = classification
        model.commit()
        return model

    def update_attributes(self, req, resp, eid, classification):
        # In case not all fields was submitted,
        # first we grab what we had.
        attrs = infinitystone_element_classifications()
        attrs.sql_id(classification)
        classification = attrs['classification']
        obj = EntryPoints('tachyonic.element.classifications')[
            classification]()
        obj.update(js.loads(attrs['metadata']))
        obj.update(req.json)
        attrs['metadata'] = obj.json
        attrs.commit()

        return obj.dict

    def delete_attributes(self, req, resp, eid, classification):
        attr = obj(req, infinitystone_element_classifications,
                   sql_id=classification)
        attr.sql_id(classification)
        attr.commit()
        return attr


@register.resources()
class Interfaces():
    def __init__(self):
        router.add('GET',
                   '/v1/interfaces',
                   self.list,
                   tag='infrastructure:view')

    def list(self, req, resp):
        """Lists all interfaces registered under the
        tachyonic.element.interfaces entry point.
        """
        interfaces = []
        for e in EntryPoints('tachyonic.element.interfaces'):
            interfaces.append({'id': e, 'name': e})
        return raw_list(req, interfaces)


@register.resources()
class Classifications():
    def __init__(self):
        router.add('GET',
                   '/v1/classifications',
                   self.list,
                   tag='infrastructure:view')

    def list(self, req, resp):
        """Lists all the registered element_attributes Entrypoints.
        """
        classifications = []
        for e in EntryPoints('tachyonic.element.classifications'):
            classifications.append({'id': e, 'name': e})
        return raw_list(req, classifications)
