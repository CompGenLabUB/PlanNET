"""
Models of PlanNet
"""

from __future__ import unicode_literals
from django.db import models
from py2neo import Graph
import json


graph = Graph("http://localhost:7474/db/data/")



# QUERIES
# ------------------------------------------------------------------------------
PREDNODE_QUERY = """
    MATCH (n:%s)-[r:HOMOLOG_OF]-(m:Human)
    WHERE  n.symbol = "%s"
    RETURN n.symbol AS symbol,
        n.sequence AS sequence,
        n.orf AS orf,
        m.symbol AS human,
        r.blast_cov AS blast_cov,
        r.blast_eval AS blast_eval,
        r.nog_brh AS nog_brh,
        r.pfam_sc AS pfam_sc,
        r.nog_eval AS nog_eval,
        r.blast_brh AS blast_brh,
        r.pfam_brh AS pfam_brh LIMIT 1
"""

# ------------------------------------------------------------------------------
HUMANNODE_QUERY = """
    MATCH (n:%s)
    WHERE n.symbol = "%s"
    RETURN n.symbol AS symbol
"""

# ------------------------------------------------------------------------------
PREDINTERACTION_QUERY = """
    MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)
    WHERE n.symbol = '%s' AND m.symbol = '%s'
    RETURN r.int_prob     AS int_prob,
        r.path_length  AS path_length,
        r.cellcom_nto  AS cellcom_nto,
        r.molfun_nto   AS molfun_nto,
        r.bioproc_nto  AS bioproc_nto,
        r.dom_int_sc   AS dom_int_sc
        LIMIT 1
"""

# ------------------------------------------------------------------------------
NEIGHBOURS_QUERY = """
    MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)-[s:HOMOLOG_OF]-(l:Human)
    WHERE  n.symbol = '%s'
    RETURN m.symbol         AS target,
        m.orf            AS torf,
        m.sequence       AS tsequence,
        l.symbol         AS human,
        r.int_prob       AS int_prob,
        r.path_length    AS path_length,
        r.cellcom_nto    AS cellcom_nto,
        r.molfun_nto     AS molfun_nto,
        r.bioproc_nto    AS bioproc_nto,
        r.dom_int_sc     AS dom_int_sc,
        s.blast_cov      AS blast_cov,
        s.blast_eval     AS blast_eval,
        s.nog_brh        AS nog_brh,
        s.pfam_sc        AS pfam_sc,
        s.nog_eval       AS nog_eval,
        s.blast_brh      AS blast_brh,
        s.pfam_brh       AS pfam_brh
"""

# ------------------------------------------------------------------------------
SHORTESTPATH_QUERY = """
    MATCH p=allShortestPaths( (n:%s)-[:INTERACT_WITH*]-(m:%s) )
    WHERE n.symbol = '%s'
    AND m.symbol = '%s'
"""

# ------------------------------------------------------------------------------
DOMAIN_QUERY = """
    MATCH (n:%s)-[r]->(dom:Pfam)
    WHERE n.symbol = '%s'
    RETURN dom.accession   AS accession,
           dom.description AS description,
           dom.identifier  AS identifier,
           dom.mlength     AS mlength,
           r.pfam_start    AS p_start,
           r.pfam_end      AS p_end,
           r.s_start       AS s_start,
           r.s_end         AS s_end,
           r.perc          AS perc
"""

# ------------------------------------------------------------------------------
HOMOLOGS_QUERY = """
    MATCH (n:Human)-[r:HOMOLOG_OF]-(m:%s)
    WHERE  n.symbol = "%s"
    RETURN n.symbol AS human,
        m.symbol AS homolog,
        r.blast_cov AS blast_cov,
        r.blast_eval AS blast_eval,
        r.nog_brh AS nog_brh,
        r.pfam_sc AS pfam_sc,
        r.nog_eval AS nog_eval,
        r.blast_brh AS blast_brh,
        r.pfam_brh AS pfam_brh
"""

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
        self.domains    = list()
        if self.database not in self.allowed_databases:
            raise IncorrectDatabase(self.database)

    def __query_node(self):
        """
        This method will be overriden by HumanNode or PredictedNode.
        It will query the Neo4j database and it will get the required node.
        """


    def path_to_node(self, target, including=None, excluding=None):
        """
        Given a target node object, this method finds all the shortest paths to that node,
        if there aren't any, it returns None.
        It returns a list of dictionaries, each of them with two keys:
            'graph': GraphCytoscape object with the graph of the path
            'score': Score of the given path.
        """
        query = SHORTESTPATH_QUERY % (self.database, target.database, self.symbol, target.symbol)
        query += """RETURN DISTINCT p,
                    reduce(int_prob = 0.0, r IN relationships(p) | int_prob + toFloat(r.int_prob))/length(p) AS total_prob"""
        results = graph.run(query).data()

        if results:
            paths = list()

            for path in results:
                nodes_obj_in_path = list()
                rels_obj_in_path  = list()
                nodes_in_path     = path['p'].nodes()
                rels_in_path      = path['p'].relationships()
                path_score        = path['total_prob']
                rel_properties    = None

                for idx, node in enumerate(nodes_in_path):
                    symbol   = node.properties['symbol']
                    current_node = PredictedNode(
                                symbol   = symbol,
                                database = self.database,
                    )
                    nodes_obj_in_path.append(current_node)
                    if idx > 0:
                        # Add relationship between node[idx] and node[idx - 1]
                        rels_obj_in_path.append(PredInteraction(
                            source_symbol = nodes_obj_in_path[idx - 1].symbol,
                            target        = current_node,
                            database      = self.database,
                            parameters    = rel_properties
                        ))

                    if idx < len(rels_in_path):
                        rel_properties = rels_in_path[idx]
                        rel_properties['path_length'] = int(rel_properties['path_length'])
                graphobj = GraphCytoscape()
                graphobj.add_elements(nodes_obj_in_path)
                graphobj.add_elements(rels_obj_in_path)
                paths.append({'graph': graphobj, 'score': path_score })
            # Sort paths by score
            return paths
        else:
            # No results
            print("No paths")
            return None

    def get_domains(self):
        """
        This will return a list of Has_domain objects or, if the sequence has no Pfam domains,
        a None object.
        """
        query = DOMAIN_QUERY % (self.database, self.symbol)

        results = graph.run(query)
        results = results.data()

        if results:
            annotated_domains = list()
            for row in results:
                domain = Domain(
                    accession   = row['accession'],
                    description = row['description'],
                    identifier  = row['identifier'],
                    mlength     = row['mlength']
                )
                domain_annotation = HasDomain(
                    node    = self,
                    domain  = domain,
                    p_start = row['p_start'],
                    p_end   = row['p_end'],
                    s_start = row['s_start'],
                    s_end   = row['s_end'],
                    perc    = row['perc']
                )
                annotated_domains.append(domain_annotation)
            print(annotated_domains)
            annotated_domains.sort(key=lambda x: x.s_start)
            self.domains = annotated_domains
            print(annotated_domains)
            return self.domains
        else:
            self.domains = None
            return self.domains

# ------------------------------------------------------------------------------
class Homology(object):
    """
    Class for homology relationships between a PredictedNode and a HumanNode.
    """
    def __init__(self,  human, blast_cov, blast_eval, nog_brh,  pfam_sc, nog_eval, blast_brh, pfam_brh, prednode=None):
        self.prednode   = prednode
        self.human      = human
        self.blast_cov  = blast_cov
        self.blast_eval = blast_eval
        self.nog_brh    = nog_brh
        self.pfam_sc    = pfam_sc
        self.nog_eval   = nog_eval
        self.blast_brh  = blast_brh
        self.pfam_brh   = pfam_brh


# ------------------------------------------------------------------------------
class Domain(object):
    """
    Class for Pfam domains.
    """
    def __init__(self, accession, description, identifier, mlength):
        self.accession   = accession
        self.description = description
        self.identifier  = identifier
        self.mlength     = mlength

# ------------------------------------------------------------------------------
class HasDomain(object):
    """
    Class for relationships between a node and a Pfam domain annotated on the sequence.
    """
    def __init__(self, domain, node, p_start, p_end, s_start, s_end, perc):
        self.domain  = domain
        self.node    = node
        self.p_start = int(p_start)
        self.p_end   = int(p_end)
        self.s_start = int(s_start)
        self.s_end   = int(s_end)
        self.perc    = perc

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
        query = PREDINTERACTION_QUERY % (self.database, self.database, self.source_symbol, self.target.symbol)

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

    def to_jsondict(self):
        '''
        This function takes a PredInteraction object and returns a dictionary with the necessary
        structure to convert it to json and be read by cytoscape.js
        '''
        element         = dict()
        element['data'] = dict()
        element['data']['id']          = "-".join(sorted((self.source_symbol, self.target.symbol)))
        element['data']['source']      = self.source_symbol
        element['data']['target']      = self.target.symbol
        element['data']['pathlength']  = self.parameters['path_length']
        element['data']['probability'] = self.parameters['int_prob']

        if self.parameters['path_length'] == 1:
            element['data']['colorEDGE']   = "#72a555"
        else:
            element['data']['colorEDGE']   = "#CA6347"

        return element


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
        query = HUMANNODE_QUERY % (self.database, self.symbol)

        results = graph.run(query)
        results = results.data()
        if results:
            for row in results:
                self.symbol   = row["symbol"]
        else:
            raise NodeNotFound(self.symbol, self.database)

    def get_homologs(self, database):
        """
        Gets all homologs of the specified database. Returns a LIST of Homology objects.
        """
        query = HOMOLOGS_QUERY % (database, self.symbol)

        results  = graph.run(query)
        results  = results.data()
        homologs = list()
        if results:
            for row in results:
                try:
                    homolog_node = PredictedNode(row['homolog'], database)
                except:
                    continue
                homolog_rel    = Homology(
                    prednode   = homolog_node,
                    human      = self.symbol,
                    blast_cov  = row['blast_cov'],
                    blast_eval = row['blast_eval'],
                    nog_brh    = row['nog_brh'],
                    pfam_sc    = row['pfam_sc'],
                    nog_eval   = row['nog_eval'],
                    blast_brh  = row['blast_brh'],
                    pfam_brh   = row['pfam_brh']
                )
                homologs.append(homolog_rel)
            return homologs
        else:
            print("NO HOMOLOGS")
            return None


# ------------------------------------------------------------------------------
class PredictedNode(Node):
    """
    Class for planarian nodes.
    """
    allowed_databases = set(["Cthulhu", "Consolidated"])

    def __init__(self, symbol, database, sequence=None, orf=None, homolog=None, important=False):
        super(PredictedNode, self).__init__(symbol, database)
        self.sequence       = sequence
        self.orf            = orf
        self.homolog        = homolog
        self.important      = important
        self.gccont         = None
        self.length         = None

        if sequence is None:
            self.__query_node()

    def get_summary(self):
        '''
        Fills attribute values that are not mandatory, with a summary of several
        features of the node
        '''
        self.length = len(self.sequence)
        self.gccont = ( self.sequence.count("G") + self.sequence.count("C") ) / self.length

    def __query_node(self):
        "Gets node from neo4j and fills sequence, orf and length attributes."
        query = PREDNODE_QUERY % (self.database, self.symbol)

        results = graph.run(query)
        results = results.data()

        if results:
            for row in results:
                # Add node
                self.symbol         = row["symbol"]
                self.sequence       = row['sequence']
                self.orf            = row["orf"]

                # Add homolog
                human_node = HumanNode(row['human'], "Human")
                self.homolog = Homology(
                    prednode   = self,
                    human      = human_node,
                    blast_cov  = row['blast_cov'],
                    blast_eval = row['blast_eval'],
                    nog_brh    = row['nog_brh'],
                    pfam_sc    = row['pfam_sc'],
                    nog_eval   = row['nog_eval'],
                    blast_brh  = row['blast_brh'],
                    pfam_brh   = row['pfam_brh']
                )
        else:
            print("NOTFOUND")
            raise NodeNotFound(self.symbol, self.database)

    def to_jsondict(self):
        '''
        This function takes a node object and returns a dictionary with the necessary
        structure to convert it to json and be read by cytoscape.js
        '''
        element                     = dict()
        element['data']             = dict()
        element['data']['id']       = self.symbol
        element['data']['name']     = self.symbol
        element['data']['database'] = self.database
        element['data']['homolog']  = self.homolog.human.symbol
        if self.important:
            element['data']['colorNODE'] = "#449D44"
        else:
            element['data']['colorNODE'] = "#404040"
        return element

    def get_neighbours(self):
        """
        Method to get the adjacent nodes in the graph.
        Fills attribute neighbours, which will be a list of PredInteraction objects.
        """
        query = NEIGHBOURS_QUERY % (self.database, self.database, self.symbol)
        results = graph.run(query)
        results = results.data()
        if results:
            for row in results:
                parameters = dict()
                # Initialize parameters to pass to the PredInteraction object
                parameters = {
                    'int_prob'    : round(float(row['int_prob']), 3),
                    'path_length' : round(float(row['path_length']), 3),
                    'cellcom_nto' : round(float(row['cellcom_nto']), 3),
                    'molfun_nto'  : round(float(row['molfun_nto']), 3),
                    'bioproc_nto' : round(float(row['bioproc_nto']), 3),
                    'dom_int_sc'  : round(float(row['dom_int_sc']), 3)
                }
                # Homology object
                human_node = HumanNode(row['human'], "Human")
                thomolog  = Homology(
                    human      = human_node,        blast_cov = row['blast_cov'],
                    blast_eval = row['blast_eval'], nog_brh = row['nog_brh'],
                    pfam_sc    = row['pfam_sc'],    nog_eval   = row['nog_eval'],
                    blast_brh  = row['blast_brh'],  pfam_brh   = row['pfam_brh']
                )
                # Node Object
                target = PredictedNode(
                    symbol   = row['target'],    database = self.database,
                    sequence = row['tsequence'], orf      = row['torf'],
                    homolog  = thomolog
                )

                # Add prednode to homology object
                target.homolog.prednode = target

                # Interaction Object
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
        return self.neighbours

    def get_graphelements(self, including=None):
        """
        Returns a list of nodes and edges adjacent to the node.
        """
        nodes = list()
        edges = list()
        added_elements = set()
        if not self.neighbours:
            self.get_neighbours()
        nodes.append(self)
        added_elements.add(self.symbol)
        for interaction in self.neighbours:
            if including and interaction.target.symbol not in including:
                continue
            if interaction.target.symbol not in added_elements:
                added_elements.add(interaction.target.symbol)
                nodes.append( interaction.target )
            if (interaction.target.symbol, self.symbol) not in added_elements:
                added_elements.add((self.symbol, interaction.target.symbol))
                edges.append( interaction )
        return nodes, edges

# ------------------------------------------------------------------------------
class GraphCytoscape(object):
    """
    Class for a graph object
    """
    def __init__(self):
        self.nodes = list()
        self.edges = list()

    def add_elements(self, elements):
        """
        Method that takes a list of node or PredInteraction objects and adds them
        to the grah.
        """
        for element in elements:
            if isinstance(element, Node):
                self.nodes.append( element )
            elif isinstance(element, PredInteraction):
                self.edges.append( element )
            else:
                raise WrongGraphObject(element)

    def add_node(self, node):
        """
        Adds a single node to the graph
        """
        self.add_elements([node])

    def add_interaction(self, interaction):
        """
        Adds a single interaction to the graph
        """
        self.add_elements([interaction])

    def define_important(self, vip_nodes):
        """
        Gets a list of nodes and defines them as important
        """
        for node in self.nodes:
            if node.symbol in vip_nodes:
                node.important = True

    def to_json(self):
        """
        Converts the graph to a json string to add it to cytoscape.js
        """
        graphelements = {
            'nodes': [node.to_jsondict() for node in self.nodes],
            'edges': [edge.to_jsondict() for edge in self.edges]
        }
        graphelements = json.dumps(graphelements)
        return graphelements

    def filter(self, including):
        """
        Filters nodes and edges from the graph
        """
        nodes_to_keep = list()
        edges_to_keep = list()
        for node in self.nodes:
            if node.symbol in including:
                nodes_to_keep.append(node)
            else:
                continue
        for edge in self.edges:
            if edge.source_symbol in including and edge.target.symbol in including:
                edges_to_keep.append(edge)
            else:
                continue
        self.nodes = nodes_to_keep
        self.edges = edges_to_keep
        return

# ------------------------------------------------------------------------------
class Document(models.Model):
    """
    Class for Documents uploaded to the server.
    """
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')


# EXCEPTIONS
# ------------------------------------------------------------------------------
class IncorrectDatabase(Exception):
    """Exception raised when incorrect database"""
    def __init__(self, database):
        self.database = database

    def __str__(self):
        return "%s database not found, incorrect database name." % self.database

# ------------------------------------------------------------------------------
class WrongGraphObject(Exception):
    """Exception for wrong graph object given to add_[node|edge]"""
    def __init__(self, obj):
        self.type = type(obj)
    def __str__(self):
        return "Can't add object of type %s to GraphCytoscape object." % self.type

# ------------------------------------------------------------------------------
class NodeNotFound(Exception):
    """Exception raised when a node is not found on the db"""
    def __init__(self, symbol, database):
        self.symbol = symbol
    def __str__(self):
        return "Symbol %s not found in database %s." % (self.pnode.symbol, self.pnode.database)

# ------------------------------------------------------------------------------
class NoHomologFound(Exception):
    """Exception raised when a node homolog is not found. Internal error. Should not happen"""
    def __init__(self, symbol):
        self.symbol = symbol
    def __str__(self):
        return "Homolog of %s not found in database." % (self.symbol)
