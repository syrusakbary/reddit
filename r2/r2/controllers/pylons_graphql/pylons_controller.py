from __future__ import absolute_import

from pylons import Response, request, tmpl_context as c

from .base import GraphQLBase


class GraphQLController(GraphQLBase):
    response_class = Response

    def get_context(self, request):
        if self.context is not None:
            return self.context
        return c

    def index(self):
        return self.dispatch_request(request)
