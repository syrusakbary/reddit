import json

import six
from pylons import Response, request, tmpl_context as c

from graphql import Source, execute, parse, validate
from graphql.error import format_error as format_graphql_error
from graphql.error import GraphQLError
from graphql.execution import ExecutionResult
from graphql.type.schema import GraphQLSchema
from graphql.utils.get_operation_ast import get_operation_ast

from .render_graphiql import render_graphiql


class HttpError(Exception):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super(HttpError, self).__init__(message, *args, **kwargs)


class BadRequest(HttpError):
    status_code = 400


class MethodNotAllowed(HttpError):
    status_code = 405


class GraphQLController(object):
    schema = None
    executor = None
    root_value = None
    context = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    middleware = None
    batch = False

    methods = ['GET', 'POST', 'PUT', 'DELETE']

    def __init__(self, **kwargs):
        super(GraphQLController, self).__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        assert not all((self.graphiql, self.batch)), 'Use either graphiql or batch processing'
        assert isinstance(self.schema, GraphQLSchema), 'A Schema is required to be provided to GraphQLView.'

    # noinspection PyUnusedLocal
    def get_root_value(self, request):
        return self.root_value

    def get_context(self, request):
        if self.context is not None:
            return self.context
        return c

    def get_middleware(self, request):
        return self.middleware

    def render_graphiql(self, *args, **kwargs):
        return render_graphiql(*args, **kwargs)

    def get_executor(self, request):
        return self.executor

    def index(self):
        return self.dispatch_request(request)

    def dispatch_request(self, request):
        try:
            if request.method.lower() not in ('get', 'post'):
                raise MethodNotAllowed(['GET', 'POST'], 'GraphQL only supports GET and POST requests.')

            data = self.parse_body(request)
            show_graphiql = self.graphiql and self.can_display_graphiql(request, data)

            if self.batch:
                responses = [self.get_response(request, entry) for entry in data]
                result = '[{}]'.format(','.join([response[0] for response in responses]))
                status_code = max(responses, key=lambda response: response[1])[1]
            else:
                result, status_code = self.get_response(request, data, show_graphiql)

            if show_graphiql:
                query, variables, operation_name, id = self.get_graphql_params(request, data)
                return self.render_graphiql(
                    graphiql_version=self.graphiql_version,
                    graphiql_template=self.graphiql_template,
                    query=query,
                    variables=variables and self.json_encode(request, variables, True),
                    operation_name=operation_name,
                    result=result
                )

            return Response(
                result,
                status=status_code,
                content_type='application/json'
            )

        except HttpError as e:
            return Response(
                self.json_encode(request, {
                    'errors': [self.format_error(e)]
                }),
                # status_int=e.status_code,
                headerlist=[('Allow', 'GET, POST')],
                content_type='application/json'
            )

    def get_response(self, request, data, show_graphiql=False):
        query, variables, operation_name, id = self.get_graphql_params(request, data)

        execution_result = self.execute_graphql_request(
            request,
            data,
            query,
            variables,
            operation_name,
            show_graphiql
        )

        status_code = 200
        if execution_result:
            response = {}

            if execution_result.errors:
                response['errors'] = [self.format_error(e) for e in execution_result.errors]

            if execution_result.invalid:
                # status_code = 400
                status_code = 200
            else:
                status_code = 200
                response['data'] = execution_result.data

            if self.batch:
                response = {
                    'id': id,
                    'payload': response,
                    'status': status_code,
                }

            result = self.json_encode(request, response, show_graphiql)
        else:
            result = None

        return result, status_code

    def json_encode(self, request, d, show_graphiql=False):
        pretty = self.pretty or show_graphiql or request.params.get('pretty')
        if not pretty:
            return json.dumps(d, separators=(',', ':'))

        return json.dumps(d,
                          indent=2, separators=(',', ': '))

    # noinspection PyBroadException
    def parse_body(self, request):
        content_type = self.get_content_type(request)
        if content_type == 'application/graphql':
            return {'query': request.data.decode()}

        elif content_type == 'application/json':
            try:
                request_json = request.json_body
                if self.batch:
                    assert isinstance(request_json, list)
                else:
                    assert isinstance(request_json, dict)
                return request_json
            except:
                raise BadRequest('POST body sent invalid JSON.')

        elif content_type == 'application/x-www-form-urlencoded':
            return request.form

        elif content_type == 'multipart/form-data':
            return request.form

        return {}

    def execute(self, *args, **kwargs):
        return execute(self.schema, *args, **kwargs)

    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        if not query:
            if show_graphiql:
                return None
            raise BadRequest('Must provide query string.')

        try:
            source = Source(query, name='GraphQL request')
            ast = parse(source)
            validation_errors = validate(self.schema, ast)
            if validation_errors:
                return ExecutionResult(
                    errors=validation_errors,
                    invalid=True,
                )
        except Exception as e:
            return ExecutionResult(errors=[e], invalid=True)

        if request.method.lower() == 'get':
            operation_ast = get_operation_ast(ast, operation_name)
            if operation_ast and operation_ast.operation != 'query':
                if show_graphiql:
                    return None
                raise MethodNotAllowed(
                    ['POST'], 'Can only perform a {} operation from a POST request.'.format(operation_ast.operation)
                )

        try:
            return self.execute(
                ast,
                root_value=self.get_root_value(request),
                variable_values=variables or {},
                operation_name=operation_name,
                context_value=self.get_context(request),
                middleware=self.get_middleware(request),
                executor=self.get_executor(request)
            )
        except Exception as e:
            return ExecutionResult(errors=[e], invalid=True)

    @classmethod
    def can_display_graphiql(cls, request, data):
        raw = 'raw' in request.params or 'raw' in data
        return not raw and cls.request_wants_html(request)

    @classmethod
    def request_wants_html(cls, request):
        best = request.accept \
            .best_match(['application/json', 'text/html'])
        return best == 'text/html' and \
            request.accept.quality(best) > \
            request.accept.quality('application/json')

    @staticmethod
    def get_graphql_params(request, data):
        query = request.params.get('query') or data.get('query')
        variables = request.params.get('variables') or data.get('variables')
        id = request.params.get('id') or data.get('id')

        if variables and isinstance(variables, six.text_type):
            try:
                variables = json.loads(variables)
            except:
                raise BadRequest('Variables are invalid JSON.')

        operation_name = request.params.get('operationName') or data.get('operationName')

        return query, variables, operation_name, id

    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLError):
            return format_graphql_error(error)

        return {'message': six.text_type(error)}

    @staticmethod
    def get_content_type(request):
        # We use mimetype here since we don't need the other
        # information provided by content_type
        return request.content_type
