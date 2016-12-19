import graphene

from r2.lib.graphql.user import User
from r2.lib.graphql.subreddit import Subreddit
from r2.lib.graphql.node import Node

from r2.models.subreddit import Frontpage, All, Random

class Query(graphene.ObjectType):

    viewer = graphene.Field(User)
    front = graphene.Field(Subreddit)
    all = graphene.Field(Subreddit)
    random = graphene.Field(Subreddit)
    node = Node.Field()

    def resolve_viewer(self, args, context, info):
        return context.user

    def resolve_front(self, args, context, info):
        return Frontpage

    def resolve_all(self, args, context, info):
        return All

    def resolve_random(self, args, context, info):
        return Random


schema = graphene.Schema(query=Query, types=[Subreddit])
