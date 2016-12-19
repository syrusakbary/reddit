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
from pylons import request, response
from pylons import app_globals as g
from pylons.i18n import _, ungettext

from r2.controllers.reddit_base import MinimalController, RedditController


from r2.lib.pages import BoringPage, GraphQL as GraphQLPage
from r2.lib.csrf import csrf_exempt
from r2.lib.graphql import schema

from pylons_graphql import GraphQL


class GraphQLController(GraphQL(RedditController)):
    schema = schema

    def GET_graphql(self):
        self.dispatch_request()

    @csrf_exempt
    def POST_graphql(self):
        return self.dispatch_request()

    def GET_explorer(self):
        data = self.parse_body(request)
        result, status_code = self.get_response(request, data, True)
        query, variables, operation_name, id = self.get_graphql_params(request, data)

        # return self.render_graphiql(
        #     graphiql_version=self.graphiql_version,
        #     graphiql_template=self.graphiql_template,
        #     query=query,
        #     variables=variables,
        #     graphql_url='/api/graphql',
        #     operation_name=operation_name,
        #     result=result
        # )

        return BoringPage(_("graphql explorer"),
            content=GraphQLPage(
                query=query,
                variables=variables,
                graphql_url='/api/graphql',
                operation_name=operation_name,
                result=result,
            ),
            show_sidebar=False,
            show_infobar=False
        ).render()
