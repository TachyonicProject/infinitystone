# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Christiaan Frans Rademan <chris@fwiw.co.za>. David Kruger.
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
from luxon import SQLModel
from luxon.utils.timezone import now


@register.model()
class infinitystone_element(SQLModel):
    id = SQLModel.Uuid(default=uuid4, internal=True)
    domain = SQLModel.Fqdn(internal=True)
    tenant_id = SQLModel.Uuid(internal=True)
    parent_id = SQLModel.Uuid()
    name = SQLModel.String(null=False)
    enabled = SQLModel.Boolean(default=True)
    creation_time = SQLModel.DateTime(default=now, readonly=True)
    element_parent = SQLModel.ForeignKey(parent_id, id, on_delete='RESTRICT')
    unique_element = SQLModel.UniqueIndex(name, domain, tenant_id)
    primary_key = id


@register.model()
class infinitystone_element_interface(SQLModel):
    id = SQLModel.Uuid(default=uuid4, internal=True)
    element_id = SQLModel.Uuid(null=False)
    interface = SQLModel.String(null=False)
    metadata = SQLModel.MediumText()
    creation_time = SQLModel.DateTime(default=now, readonly=True)
    element_int_ref = SQLModel.ForeignKey(element_id, infinitystone_element.id)
    unique_element_interface = SQLModel.UniqueIndex(element_id, interface)
    element_driver = SQLModel.Index(element_id, interface)
    primary_key = id

@register.model()
class infinitystone_element_classifications(SQLModel):
    id = SQLModel.Uuid(default=uuid4, internal=True)
    element_id = SQLModel.Uuid(null=False)
    classification = SQLModel.String(null=False)
    metadata = SQLModel.MediumText()
    creation_time = SQLModel.DateTime(default=now, readonly=True)
    em_attr_ref = SQLModel.ForeignKey(element_id, infinitystone_element.id)
    primary_key = id

@register.model()
class infinitystone_element_tag(SQLModel):
    id = SQLModel.Uuid(default=uuid4, internal=True)
    name = SQLModel.String(null=False)
    element_id = SQLModel.Uuid(null=False)
    element_tag_ref = SQLModel.ForeignKey(element_id, infinitystone_element.id)
    # Need the following in order to be able to insert tag=NULL
    unique_element_tag = SQLModel.UniqueIndex(name)
    primary_key = id
