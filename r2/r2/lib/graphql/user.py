import graphene

from r2.models.account import Account
from r2.models.subreddit import Subreddit as SubredditModel

from r2.lib.graphql.node import Node
from r2.lib.graphql.subreddit import Subreddit


class Redditor(graphene.ObjectType):
    class Meta:
        interfaces = (Node, )

    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    comment_karma = graphene.Int()
    link_karma = graphene.Int()

    def resolve_id(self, args, context, info):
        return self._fullname

    @staticmethod
    def is_type_of(root, context, info):
        return isinstance(root, Account)


class SubredditKarma(graphene.ObjectType):
    subreddit = graphene.Field(Subreddit)
    comment_karma = graphene.Int()
    link_karma = graphene.Int()


class User(graphene.ObjectType):
    me = graphene.Field(Redditor, required=True)
    karma = graphene.List(SubredditKarma)
    subreddits = graphene.List(Subreddit)

    friends = graphene.List(lambda: Redditor)
    blocked = graphene.List(lambda: Redditor)

    @staticmethod
    def is_type_of(root, context, info):
        return isinstance(root, Account)

    def resolve_me(self, args, context, info):
        return self

    def resolve_karma(self, args, context, info):
        karma = []
        for sr, (link_karma, comment_karma) in self.all_karmas():
            subreddit = SubredditModel._byID(sr)
            karma.append(SubredditKarma(
                subreddit=subreddit,
                comment_karma=comment_karma,
                link_karma=link_karma
            ))
        return karma

    def resolve_subreddits(self, args, context, info):
        return map(SubredditModel._byID, self.subreddits)

    def resolve_friends(self, args, context, info):
        return map(Account._byID, self.friends)

    def resolve_blocked(self, args, context, info):
        return map(Account._byID, self.enemies)
