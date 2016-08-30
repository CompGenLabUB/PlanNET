from __future__ import unicode_literals

from django.db import models
from py2neo import Graph, Path


graph = Graph("http://localhost:7474/db/data/")


# NEO4J CLASSES

# ------------------------------------------------------------------------------
class Node(object):
    """
    Base class for all the nodes in the database.
    """

    def __init__(self, symbol, database):
        super(Node, self).__init__()
        self.symbol   = symbol
        self.database = database.capitalize()
        if self.database not in self.allowed_databases:
            raise IncorrectDatabase(self.database)

    def __query_node(self):
        """
        This method will be overriden by HumanNode or PredictedNode.
        It will query the Neo4j database and it will get the required node.
        """

    def get_neighbours(self):
        """
        Method to get the adjacent nodes in the graph.
        """
        pass

    def path_to_node(self, target):
        """
        Given a target node, this method finds all the shortest paths to that node,
        if there aren't any, it returns None.
        """
        pass

# ------------------------------------------------------------------------------
class HumanNode(Node):
    """
    Human node class definition.
    """

    allowed_databases = set(["Human"])

    def __init__(self, symbol, database):
        super(HumanNode, self).__init__(symbol, database)
        self.__query_node()

    def __query_node(self):
        print("I'm in Human")
        query = """
            MATCH (n:%s)
            WHERE n.symbol = "%s"
            RETURN n.symbol AS symbol
        """ % (self.database, self.symbol)

        print(query)
        results = graph.run(query)
        results = results.data()
        if results:
            for row in results:
                self.symbol   = row["symbol"]
        else:
            raise NodeNotFound(self)


# ------------------------------------------------------------------------------
class PredictedNode(Node):
    """
    Class for planarian nodes.
    """

    allowed_databases = set(["Cthulhu", "Consolidated"])

    def __init__(self, symbol, database):
        super(PredictedNode, self).__init__(symbol, database)
        self.sequence = None
        self.orf      = None
        self.length   = None
        self.__query_node()

    def __query_node(self):
        "Gets node from neo4j and fills sequence, orf and length attributes."
        query = """
            MATCH (n:%s)
            WHERE  n.symbol = "%s"
            RETURN n.symbol AS symbol, n.sequence AS sequence, n.orf AS orf LIMIT 1
        """ % (self.database, self.symbol)

        results = graph.run(query)
        results = results.data()

        if results:
            for row in results:
                self.symbol   = row["symbol"]
                self.sequence = row['sequence']
                self.orf      = row["orf"]
        else:
            raise NodeNotFound(self)



# EXCEPTIONS
# ------------------------------------------------------------------------------
class IncorrectDatabase(Exception):
    """Exception raised when incorrect database"""
    def __init__(self, database):
        self.database = database

    def __str__(self):
        return "%s database not found, incorrect database name." % self.database

# ------------------------------------------------------------------------------
class NodeNotFound(Exception):
    """Exception raised when a node is not found on the db"""
    def __init__(self, pnode):
        self.pnode = pnode

    def __str__(self):
        return "Symbol %s not found in database %s." % (self.pnode.symbol, self.pnode.database)
