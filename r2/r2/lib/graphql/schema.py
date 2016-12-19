import graphene

from r2.lib.graphql.user import User
from r2.lib.graphql.subreddit import Subreddit
from r2.lib.graphql.node import Node

class Query(graphene.ObjectType):

    viewer = graphene.Field(User)
    node = Node.Field()

    def resolve_viewer(self, args, context, info):
        return context.user


schema = graphene.Schema(query=Query, types=[Subreddit])
