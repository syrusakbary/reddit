import graphene

from r2.lib.db.thing import Thing


class Node(graphene.Node):

    class Meta:
        name = 'Node'

    @staticmethod
    def to_global_id(type, id):
        return id

    @staticmethod
    def get_node_from_global_id(global_id, context, info):
        return Thing._by_fullname(global_id)
