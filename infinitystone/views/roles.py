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
from luxon import db
from luxon import GetLogger
from luxon import register_resource

from infinitystone.utils.api import model
from infinitystone.models.roles import luxon_role

log = GetLogger(__name__)

@register_resource('GET', '/v1/roles', tag='admin')
def roles(req, resp):
    roles = model(luxon_role)
    return roles

@register_resource('POST', '/v1/role', tag='admin')
def new_role(req, resp):
    role = model(luxon_role, values=req.json)
    role.commit()
    return role

@register_resource([ 'PUT', 'PATCH' ], '/v1/role/{id}', tag='admin')
def update_role(req, resp, id):
    role = model(luxon_role, id=id, values=req.json)
    role.commit()
    return role

@register_resource('GET', '/v1/role/{id}', tag='admin')
def view_role(req, resp, id):
    role = model(luxon_role, id=id)
    return role

@register_resource('DELETE', '/v1/role/{id}', tag='admin')
def delete_role(req, resp, id):
    role = model(luxon_role, id=id)
    role.delete()
