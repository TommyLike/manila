# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six
from webob import exc

from manila.api.openstack import wsgi
from manila.api.views import share_servers as share_servers_views
from manila.api import xmlutil
from manila.db import api as db_api
from manila import exception
from manila.openstack.common import log as logging
from manila import policy

RESOURCE_NAME = 'share_server'
RESOURCES_NAME = 'share_servers'
LOG = logging.getLogger(__name__)
SHARE_SERVER_ATTRS = (
    'id',
    'project_id',
    'updated_at',
    'status',
    'host',
    'share_network_name',
)


def _make_share_server(elem, details=False):
    for attr in SHARE_SERVER_ATTRS:
        elem.set(attr)
    if details:
        elem.set('backend_details')


class ShareServerTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement(RESOURCE_NAME, selector=RESOURCE_NAME)
        _make_share_server(root, details=True)
        return xmlutil.MasterTemplate(root, 1)


class ShareServersTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement(RESOURCES_NAME)
        elem = xmlutil.SubTemplateElement(root, RESOURCE_NAME,
                                          selector=RESOURCES_NAME)
        _make_share_server(elem)
        return xmlutil.MasterTemplate(root, 1)


class ShareServerController(wsgi.Controller):
    """The Share Server API controller for the OpenStack API."""

    _view_builder_class = share_servers_views.ViewBuilder

    @wsgi.serializers(xml=ShareServersTemplate)
    def index(self, req):
        """Returns a list of share servers."""

        context = req.environ['manila.context']
        policy.check_policy(context, RESOURCE_NAME, 'index')

        search_opts = {}
        search_opts.update(req.GET)

        share_servers = db_api.share_server_get_all(context)
        for s in share_servers:
            s.project_id = s.share_network['project_id']
            if s.share_network['name']:
                s.share_network_name = s.share_network['name']
            else:
                s.share_network_name = s.share_network_id
        if search_opts:
            for k, v in six.iteritems(search_opts):
                share_servers = [s for s in share_servers if (hasattr(s, k) and
                    s[k] == v or k == 'share_network' and v in
                        [s.share_network['name'], s.share_network['id']])]
        return self._view_builder.build_share_servers(share_servers)

    @wsgi.serializers(xml=ShareServerTemplate)
    def show(self, req, id):
        """Return data about the requested share server."""
        context = req.environ['manila.context']
        policy.check_policy(context, RESOURCE_NAME, 'show')
        try:
            server = db_api.share_server_get(context, id)
            server.project_id = server.share_network["project_id"]
            if server.share_network['name']:
                server.share_network_name = server.share_network['name']
            else:
                server.share_network_name = server.share_network_id
        except exception.ShareServerNotFound as e:
            msg = "%s" % e
            raise exc.HTTPNotFound(explanation=msg)
        return self._view_builder.build_share_server(server)

    def details(self, req, id):
        """Return details for requested share server."""
        context = req.environ['manila.context']
        policy.check_policy(context, RESOURCE_NAME, 'details')
        try:
            db_api.share_server_get(context, id)
        except exception.ShareServerNotFound as e:
            msg = "%s" % e
            raise exc.HTTPNotFound(explanation=msg)
        details = db_api.share_server_backend_details_get(context, id)
        return self._view_builder.build_share_server_details(details)


def create_resource():
    return wsgi.Resource(ShareServerController())