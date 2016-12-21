import graphene

from r2.lib.graphql.user import User
from r2.lib.graphql.subreddit import Subreddit
from r2.lib.graphql.node import Node

from r2.models.subreddit import Frontpage, Subreddit as SubredditModel
from r2.lib.subreddit_search import search_reddits
from r2.lib.validator import sr_path_rx
from r2.lib.db.thing import NotFound


class Subreddits(graphene.ObjectType):
    default = graphene.List(Subreddit)
    recommended = graphene.List(Subreddit)
    search = graphene.List(Subreddit, query=graphene.String(required=True), over18=graphene.Boolean(default_value=True), exact=graphene.Boolean(default_value=False))

    ## Not idea yet in how to resolve the following
    # gold = graphene.List(Subreddit)
    # new = graphene.List(Subreddit)

    def resolve_default(self, args, context, info):
        return SubredditModel.default_subreddits(ids=False)

    def resolve_recommended(self, args, context, info):
        return SubredditModel.featured_subreddits()

    def resolve_search(self, args, context, info):
        query = args.get('query')
        exact = args.get('exact', False)
        over18 = args.get('over18', True)

        if query:
            query = sr_path_rx.sub('\g<name>', query.strip())

        if query and exact:
            try:
                sr = SubredditModel._by_name(query.strip())
            except NotFound:
                return []
            else:
                # not respecting include_over_18 for exact match
                return [sr]
        elif query:
            names = search_reddits(query, over18)
            return SubredditModel._by_name(names)


class Query(graphene.ObjectType):

    viewer = graphene.Field(User)

    front = graphene.Field(Subreddit)

    random_subreddit = graphene.Field(Subreddit, over18=graphene.Boolean(default_value=False))
    subreddit = graphene.Field(Subreddit, display_name=graphene.String(required=True))
    subreddits = graphene.Field(Subreddits)

    ## We need to create Comment, DomainListing, Redditor, Submission and Inbox before

    # comment = graphene.Field(Comment, id=graphene.ID()) # Get comment by id
    # domain = graphene.Field(DomainListing, domain=graphene.String()) # DomainListing
    # redditor = graphene.Field(Redditor, name=graphene.String(), id=graphene.ID())
    # submission = graphene.Field(Submission, id=graphene.ID(), path=graphene.String())
    # inbox = graphene.Field(Inbox) #? This should belong to a user

    node = Node.Field()
    nodes = graphene.List(Node, ids=graphene.List(graphene.ID))

    def resolve_viewer(self, args, context, info):
        return context.user

    def resolve_front(self, args, context, info):
        return Frontpage

    def resolve_random_subreddit(self, args, context, info):
        over18 = args.get('over18', False)
        return SubredditModel.random_reddit(over18=over18)

    def resolve_subreddit(self, args, context, info):
        display_name = args.get('display_name')
        try:
            return SubredditModel._by_name(display_name)
        except:
            return None

    def resolve_subreddits(self, args, context, info):
        return Subreddits()


schema = graphene.Schema(query=Query, types=[Subreddit])
