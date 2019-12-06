# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Christiaan Frans Rademan <chris@fwiw.co.za>.
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

from luxon import db
from luxon.utils.sql import build_where, build_like


def get_domains(user_id, page=1, limit=10, search=None):
    start = (page - 1) * limit

    sql = "SELECT DISTINCT infinitystone_domain.id AS id"
    sql += " ,infinitystone_domain.name AS name"
    sql += " FROM infinitystone_domain"
    sql += " INNER JOIN infinitystone_user_role"
    sql += " ON (infinitystone_user_role.domain ="
    sql += " infinitystone_domain.name)"
    sql += " OR (infinitystone_user_role.domain IS null"
    sql += " and infinitystone_user_role.tenant_id IS null)"
    where={"infinitystone_user_role.user_id": user_id}

    where, values = build_where(**where)
    if search:
        where2, values2 = build_like('OR', **search)
        if values2:
            where += " AND " + where2
            values += values2

    with db() as conn:
        return conn.execute(sql + 'WHERE ' + where +
                            ' LIMIT %s, %s' % (start, limit,),
                            values).fetchall()
