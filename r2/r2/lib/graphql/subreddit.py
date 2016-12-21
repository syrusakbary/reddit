import graphene

from r2.models.subreddit import Subreddit as SubredditModel, FakeSubreddit
from r2.lib.graphql.node import Node

from r2.models.account import Account


class Subreddit(graphene.ObjectType):
    class Meta:
        interfaces = (Node, )

    id = graphene.ID(required=True)

    path = graphene.String(required=True)
    name = graphene.String(required=True)

    @staticmethod
    def is_type_of(root, context, info):
        return isinstance(root, (SubredditModel, FakeSubreddit))

    def resolve_id(self, args, context, info):
        return self._fullname

    def resolve_moderators(self, args, context, info):
        moderators = getattr(self, 'moderators', [])
        return map(Account._byID, moderators)
