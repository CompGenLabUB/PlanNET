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
        self.symbol     = symbol
        self.database   = database.capitalize()
        self.neighbours = list()
        if self.database not in self.allowed_databases:
            raise IncorrectDatabase(self.database)

    def __query_node(self):
        """
        This method will be overriden by HumanNode or PredictedNode.
        It will query the Neo4j database and it will get the required node.
        """

    def get_neighbours(self):
        """
        Method to get the adjacent nodes in the graph. Attribute neighbours will
        be a list of PredInteraction objects.
        """
        query = """
            MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)
            WHERE  n.symbol = '%s'
            RETURN m.symbol      AS target,
                   r.int_prob    AS int_prob,
                   r.path_length AS path_length,
                   r.cellcom_nto AS cellcom_nto,
                   r.molfun_nto  AS molfun_nto,
                   r.bioproc_nto AS bioproc_nto,
                   r.dom_int_sc  AS dom_int_sc
        """ % (self.database, self.database, self.symbol)

        print(query)
        results = graph.run(query)
        results = results.data()

        if results:
            for row in results:
                parameters = dict()
                parameters = { # Initialize parameters to pass to the object
                    'int_prob'    : round(float(row['int_prob']), 3),
                    'path_length' : round(float(row['path_length']), 3),
                    'cellcom_nto' : round(float(row['cellcom_nto']), 3),
                    'molfun_nto'  : round(float(row['molfun_nto']), 3),
                    'bioproc_nto' : round(float(row['bioproc_nto']), 3),
                    'dom_int_sc'  : round(float(row['dom_int_sc']), 3)
                }
                target = PredictedNode(row['target'], self.database)
                interaction = PredInteraction(
                    source_symbol = self.symbol,
                    target        = target,
                    database      = self.database,
                    parameters    = parameters
                )

                # Add interaction to list of neighbours
                self.neighbours.append(interaction)

        # Sort interactions by probability
        self.neighbours = sorted(self.neighbours, key=lambda k: k.parameters['int_prob'], reverse=True)


    def path_to_node(self, target):
        """
        Given a target node, this method finds all the shortest paths to that node,
        if there aren't any, it returns None.
        """
        pass


# ------------------------------------------------------------------------------
class PredInteraction(object):
    """
    Class for predicted interactions.
    Source and target are PredictedNode attributes.
    """

    def __init__(self, source_symbol, target, database, parameters = None):
        self.source_symbol = source_symbol
        self.target        = target
        self.database      = database
        self.parameters    = parameters
        if self.parameters is None:
            self.__query_interaction()

    def __query_interaction(self):
        """
        This private method will fetch the interaction from the DB.
        """
        query = """
            MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)
            WHERE n.symbol = '%s' AND m.symbol = '%s'
            RETURN r.int_prob     AS int_prob,
                   r.path_length  AS path_length,
                   r.cellcom_nto  AS cellcom_nto,
                   r.molfun_nto   AS molfun_nto,
                   r.bioproc_nto  AS bioproc_nto,
                   r.dom_int_sc   AS dom_int_sc
            LIMIT 1
        """ % (self.database, self.database, self.source_symbol, self.target.symbol)

        results = graph.run(query)
        results = results.data()

        if results:
            for row in results:
                self.parameters['int_prob']    = row['int_prob']
                self.parameters['path_length'] = row['path_length']
                self.parameters['cellcom_nto'] = row['cellcom_nto']
                self.parameters['molfun_nto']  = row['molfun_nto']
                self.parameters['bioproc_nto'] = row['bioproc_nto']
                self.parameters['dom_int_sc']  = row['dom_int_sc']


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
        self.sequence      = None
        self.orf           = None
        self.length        = None
        self.gccont        = None
        self.n_homologs    = None
        self.n_interactors = None
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

    def get_summary(self):
        '''
        Fills attribute values that are not mandatory, with a summary of several
        features of the node
        '''
        self.length = len(self.sequence)
        self.gccont = ( self.sequence.count("G") + self.sequence.count("C") ) / self.length





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
