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
from infinitystone.models.domains import luxon_domain

log = GetLogger(__name__)

@register_resource('GET', '/v1/domains', tag='admin')
def domains(req, resp):
    domains = model(luxon_domain)
    return domains

@register_resource('POST', '/v1/domain', tag='admin')
def new_domain(req, resp):
    domain = model(luxon_domain, values=req.json)
    domain.commit()
    return domain

@register_resource([ 'PUT', 'PATCH' ], '/v1/domain/{id}', tag='admin')
def update_domain(req, resp, id):
    domain = model(luxon_domain, id=id, values=req.json)
    domain.commit()
    return domain

@register_resource('GET', '/v1/domain/{id}', tag='admin')
def view_domain(req, resp, id):
    domain = model(luxon_domain, id=id)
    return domain

@register_resource('DELETE', '/v1/domain/{id}', tag='admin')
def delete_domain(req, resp, id):
    domain = model(luxon_domain, id=id)
    domain.delete()
