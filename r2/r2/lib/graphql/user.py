import graphene

from r2.models.account import Account
from r2.lib.graphql.node import Node

class UserKarma(graphene.ObjectType):
    link = graphene.Float()
    comment = graphene.Float()

    def resolve_link(self, args, context, info):
        return self('link')

    def resolve_comment(self, args, context, info):
        return self('comment')


class User(graphene.ObjectType):
    class Meta:
        interfaces = (Node, )

    id = graphene.ID(required=True)
    name = graphene.String()
    can_create_subreddit = graphene.Boolean()
    needs_captcha = graphene.Boolean()
    karma = graphene.Field(UserKarma)
    inbox_count = graphene.Int()

    friends = graphene.List(lambda: User)
    blocked = graphene.List(lambda: User)

    @staticmethod
    def is_type_of(root, context, info):
        return isinstance(root, Account)

    def resolve_id(self, args, context, info):
        return self._fullname

    def resolve_karma(self, args, context, info):
        return self.karma

    def resolve_friends(self, args, context, info):
        return map(Account._byID, self.friends)

    def resolve_blocked(self, args, context, info):
        return map(Account._byID, self.enemies)
