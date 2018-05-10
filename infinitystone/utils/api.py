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
from luxon.utils.cast import to_list
from luxon.exceptions import ValidationError
from luxon import db

def model(ModelClass, id=None, values=None, hide=None):
    req = g.current_request
    fields = ModelClass.fields
    domain = req.token.domain
    tenant_id = req.token.tenant_id
    model_name = ModelClass.model_name
    primary_key = ModelClass.primary_key

    if id is not None or values is not None:
        model = ModelClass(model=dict, hide=hide)
    else:
        model = ModelClass(model=list, hide=hide)

    context_values = []
    context_query = []

    if 'domain' in fields:
        if domain is not None:
            context_query.append('domain = %s')
            context_values.append(domain)
        else:
            context_query.append('domain IS NULL')

    if 'tenant_id' in fields:
        if tenant_id is not None:
            if id is not None:
                context_query.append('(tenant_id = %s or id = %s)')
                context_values.append(tenant_id)
                context_values.append(tenant_id)
            else:
                context_query.append('tenant_id = %s')
                context_values.append(tenant_id)
        else:
            context_query.append('tenant_id IS NULL')

    if id is not None:
        context_query.append('%s = %%s' % primary_key.name)
        context_values.append(id)

    context_query = " AND ".join(context_query)

    search = to_list(req.query_params.get('search'))
    search_query = []
    if len(search) > 0:
        for lookin in search:
            field, val = lookin.split(":")
            if field not in fields:
                raise ValidationError("Unknown field" +
                                                 ' %s' % field +
                                                 ' in search')
            val = val.replace("'", "''")

            if isinstance(val, (int, float,)):
                search_query.append(field + ' LIKE ' + val)
            else:
                search_query.append(field + ' LIKE ' + "'" + val + "%%'")

    search_query = " OR ".join(search_query)

    sort_range_query = ''

    if req.method == 'GET':
        sort = to_list(req.query_params.get('sort'))
        if len(sort) > 0:
            ordering = []
            for order in sort:
                order_field, order_type = order.split(':')
                order_type = order_type.lower()
            if order_type != "asc" and order_type != "desc":
                raise ValidationError('Bad order for sort provided')
            if order_field not in fields:
                raise ValidationError("Unknown field '%s' in sort" %
                                                order_field)
            ordering.append("%s %s" % (order_field, order_type))

            sort_range_query += " ORDER BY %s" % ','.join(ordering)

        range = req.query_params.get('range')
        if range is not None:
            try:
                range = range.split(',')
                if len(range) == 1:
                    limit = int(range[0])
                    sort_range_query += " LIMIT %s" % limit
                if len(range) == 2:
                    begin = int(range[0])
                    limit = int(range[1])
                    sort_range_query += " LIMIT %s, %s " % (begin, limit,)
            except ValueError:
                raise ValueError('Invalid range defiend')

    with db() as conn:
        if primary_key is None:
            raise KeyError("Model %s:" % model_name +
                           " No primary key") from None

        query = "SELECT count(*) as total FROM %s" % model_name

        if context_query != '':
            query += " WHERE %s" % context_query

        if search_query != '':
            if context_query != '':
                query += ' AND '
            else:
                query += ' WHERE '
            query += "(%s)" % search_query

        crsr = conn.execute(query, context_values)
        result = crsr.fetchone()

        if result is not None:
            total_rows = result['total']

        query = "SELECT * FROM %s " % model_name

        if context_query != '':
            query += " WHERE %s" % context_query
        if search_query != '':
            if context_query != '':
                query += ' AND '
            else:
                query += ' WHERE '
            query += "(%s)" % search_query

        query += ' ' + sort_range_query

        crsr = conn.execute(query, context_values)
        result = crsr.fetchall()
        crsr.commit()

        if req.method != "POST":
            model._sql_parse(result)

        view_rows = len(result)
        filtered_rows = total_rows - view_rows

        req.response.set_header('X-Total-Rows', str(total_rows))
        req.response.set_header('X-View-Rows', str(view_rows))
        req.response.set_header('X-Filtered-Rows', str(filtered_rows))

    if values is not None:
        model.update(values)

    return model

def parse_sql_where(where):
    """Generates an SQL WHERE string.

    Will replace None's with IS NULL's.

    Args:
        where (dict): Containing SQL search string
                      Eg: {"foo": 1, "bar": None}
    Returns:
        Tuple containing:
            string that can be used after WHERE in SQL statement,
            along with a list of the values.
        Eg. ("foo=? AND bar IS NULL", [ 1 ])
    """
    vals = []
    query = []
    for k in where:
        if where[k] is None:
            query.append(k + " IS NULL")
        else:
            query.append(k + "=?")
            vals.append(where[k])

    return (" AND ".join(query), vals)
