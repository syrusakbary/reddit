# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2015 reddit
# Inc. All Rights Reserved.
###############################################################################
from __future__ import absolute_import

from pylons import request, response
from pylons import app_globals as g
from pylons.i18n import _, ungettext
from pylons import tmpl_context as c

from r2.controllers.reddit_base import MinimalController, RedditController


from graphql.execution import ExecutionResult
from graphql.error import format_error as format_graphql_error
from graphql.error import GraphQLError

from r2.lib.base import abort
from r2.lib.pages import BoringPage, GraphQL, Password
from r2.lib.csrf import csrf_exempt
from r2.lib import utils
from r2.lib.graphql import schema
import json

from r2.lib.validator import *

# class GraphQLController(MinimalController):
class GraphQLController(RedditController):
    # def pre(self):
    #     pass

    # def post(self):
    #     pass
    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLError):
            return format_graphql_error(error)

        return {'message': str(error)}

    def get_context(self):
        return c

    def execute(self, *args, **kwargs):
        response = {}
        try:
            result = schema.execute(*args, **kwargs)
        except Exception as e:
            result = ExecutionResult(errors=[e], invalid=True)

        response['data'] = result.data
        if result.errors:
            response['errors'] = map(self.format_error, result.errors)
        
        return json.dumps(response)

    def GET_graphql(self):
        response.content_type = "text/json"

        return self.execute(
            request.params.get('query', ''),
            context_value=self.get_context(),
        )

    @csrf_exempt
    def POST_graphql(self):
        response.content_type = "text/json"

        data = request.json_body
        return self.execute(
            data.get("query", "") or "",
            operation_name=data.get("operationName"),
            variable_values=data.get("variables"),
            context_value=self.get_context(),
        )

    def GET_explorer(self):
        return BoringPage(_("graphql explorer"),
            content=GraphQL(),
            show_sidebar=False,
            show_infobar=False
        ).render()
