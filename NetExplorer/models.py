"""
Models of PlanNet
"""

from __future__ import unicode_literals
from django.db import models
from py2neo import Graph, authenticate
import json
import logging
from colour import Color
import math
import re
import time


authenticate("192.168.0.2:7473", "neo4j", "5961")
GRAPH     = Graph("https://192.168.0.2:7473/db/data/", bolt=False)
DATABASES = set([
    "Cthulhu",
    "Dresden",
    "Consolidated",
    "Newmark",
    "Graveley",
    "Illuminaplus",
    "Smed454",
    "Adamidi",
    "Blythe",
    "Pearson",
])


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
GET_CONNECTIONS_QUERY = """
    MATCH (n)-[r:INTERACT_WITH]-(m)
    WHERE n.symbol IN %s
    AND   m.symbol IN %s
    RETURN n.symbol      AS nsymbol,
           labels(n)     AS database,
           r.path_length AS path_length,
           r.int_prob    AS int_prob,
           r.dom_int_sc  AS dom_int_sc,
           r.cellcom_nto AS cellcom_nto,
           r.bioproc_nto AS bioproc_nto,
           r.molfun_nto  AS molfun_nto,
           m.symbol      AS msymbol
"""
# ------------------------------------------------------------------------------
GO_QUERY = """
    MATCH (n:Go)
    WHERE n.accession = "%s"
    RETURN n.domain as domain
"""

# ------------------------------------------------------------------------------
GO_HUMAN_NODE_QUERY = """
    MATCH (n:Go)-[:HAS_GO]-(m:Human)
    WHERE n.accession = "%s"
    RETURN n.domain as domain, m.symbol as symbol
"""

# ------------------------------------------------------------------------------
GO_HUMAN_GET_GO_QUERY = """
    MATCH (n:Go)-[:HAS_GO]-(m:Human)
    WHERE m.symbol = "%s"
    RETURN n.accession as accession, n.domain as domain ORDER BY n.domain
"""

# ------------------------------------------------------------------------------
DOMAIN_NODES_QUERY = """
    MATCH (n:%s)-[:HAS_DOMAIN]->(m:Pfam)
    WHERE m.accession = "%s"
    RETURN n.symbol as symbol
"""

# ------------------------------------------------------------------------------
EXPERIMENT_QUERY = """
    MATCH (n:Experiment)
    WHERE n.id = "%s"
    RETURN
        n.id as identifier,
        n.maxexp as maxexp,
        n.minexp as minexp,
        n.reference as reference,
        n.url       as url,
        n.percentiles as percentiles
"""

# ------------------------------------------------------------------------------
ALL_EXPERIMENTS_QUERY = """
    MATCH (n:Experiment)-[r]-(m)
    RETURN distinct keys(r) as samples, n.id as identifier, n.url as url, n.reference as reference, collect(distinct labels(m)) as datasets
"""

# ------------------------------------------------------------------------------
EXPRESSION_QUERY = """
    MATCH (n:%s)-[r:HAS_EXPRESSION]-(m:Experiment)
    WHERE n.symbol = "%s"
    AND m.id = "%s"
    RETURN r.%s as exp
"""

# ------------------------------------------------------------------------------
EXPRESSION_QUERY_GRAPH = """
    MATCH (n)-[r:HAS_EXPRESSION]-(m:Experiment)
    WHERE n.symbol IN %s
    AND m.id ="%s"
    RETURN n.symbol AS symbol, labels(n) AS database, r.%s AS exp
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
    MATCH (n:%s)-[r:INTERACT_WITH]-(m:%s)-[s:HOMOLOG_OF]-(l:Human), (m)-[t:INTERACT_WITH*0..1]-(other)
    WHERE  n.symbol = '%s'
    RETURN m.symbol         AS target,
           count(t)         AS tdegree,
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
WILDCARD_QUERY = """
    MATCH (n:%s)
    WHERE n.symbol =~ "%s"
    RETURN n.symbol AS symbol
"""

# ------------------------------------------------------------------------------
PATH_QUERY = """
    MATCH p=( (n:%s)-[r:INTERACT_WITH*%s]-(m:%s) )
    WHERE n.symbol = '%s' AND m.symbol = '%s'
    RETURN extract(nod IN nodes(p) | nod.symbol)                       AS symbols,
           extract(rel IN relationships(p) | toInt(rel.path_length))   AS path_length,
           extract(rel IN relationships(p) | toFloat(rel.int_prob))    AS int_prob,
           extract(rel IN relationships(p) | toFloat(rel.cellcom_nto)) AS cellcom_nto,
           extract(rel IN relationships(p) | toFloat(rel.molfun_nto))  AS molfun_nto,
           extract(rel IN relationships(p) | toFloat(rel.bioproc_nto)) AS bioproc_nto,
           extract(rel IN relationships(p) | toFloat(rel.dom_int_sc))  AS dom_int_sc
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
    MATCH (n:Human)-[r:HOMOLOG_OF]-(m)
    WHERE  n.symbol = "%s"
    RETURN n.symbol  AS human,
        m.symbol     AS homolog,
        r.blast_cov  AS blast_cov,
        r.blast_eval AS blast_eval,
        r.nog_brh    AS nog_brh,
        r.pfam_sc    AS pfam_sc,
        r.nog_eval   AS nog_eval,
        r.blast_brh  AS blast_brh,
        r.pfam_brh   AS pfam_brh,
        labels(m)    AS database
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


    def path_to_node(self, target, plen):
        """
        Given a target node object, this method finds all the shortest paths to that node,
        if there aren't any, it returns None.
        It returns a list of dictionaries, each of them with two keys:
            'graph': GraphCytoscape object with the graph of the path
            'score': Score of the given path.
        """
        query = PATH_QUERY % (self.database, plen, target.database, self.symbol, target.symbol)
        results = GRAPH.run(query)
        results = results.data()

        if results:
            paths = list()
            for path in results:
                nodes_in_path  = [ PredictedNode(node, self.database, query=False) for node in path['symbols']]
                relationships  = list()
                path_graph_obj = GraphCytoscape()
                for idx, val in enumerate(path['molfun_nto']):
                    parameters = dict()
                    parameters['int_prob']    = path['int_prob'][idx]
                    parameters['path_length'] = path['path_length'][idx]
                    parameters['cellcom_nto'] = path['cellcom_nto'][idx]
                    parameters['molfun_nto']  = path['molfun_nto'][idx]
                    parameters['bioproc_nto'] = path['bioproc_nto'][idx]
                    parameters['dom_int_sc']  = path['dom_int_sc'][idx]
                    relationships.append(
                        PredInteraction(
                            database      = self.database,
                            source_symbol = path['symbols'][idx],
                            target        = nodes_in_path[idx + 1],
                            parameters    = parameters
                        )
                    )
                path_graph_obj.add_elements(nodes_in_path)
                path_graph_obj.add_elements(relationships)
                paths.append(Pathway(graph=path_graph_obj))
            return paths
        else:
            # No results
            logging.info("No paths")
            return None

    def get_domains(self):
        """
        This will return a list of Has_domain objects or, if the sequence has no Pfam domains,
        a None object.
        """
        query = DOMAIN_QUERY % (self.database, self.symbol)

        results = GRAPH.run(query)
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
            annotated_domains.sort(key=lambda x: x.s_start)
            self.domains = annotated_domains
            return self.domains
        else:
            self.domains = None
            return self.domains

    def domains_to_json(self):
        """
        This function will return a json string with the information about
        the domains of the node. You have to call "get_domains()" before!
        """
        if self.domains is None:
            return None
        else:
            all_domains = [ dom.to_jsondict() for dom in self.domains ]
            json_data   = json.dumps(all_domains)
            return json_data

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
    def __init__(self, accession, description=None, identifier=None, mlength=None):
        pfam_regexp = r'PF\d{5}'
        if not re.match(pfam_regexp, accession):
            raise NotPFAMAccession(accession)
        self.accession   = accession
        self.description = description
        self.identifier  = identifier
        self.mlength     = mlength

    def get_nodes(self, database):
        query = DOMAIN_NODES_QUERY % (database, self.accession)
        results = GRAPH.run(query)
        results = results.data()
        nodes = list()
        if results:
            for row in results:
                nodes.append(row['symbol'])
            return nodes
        else:
            raise NodeNotFound(self.accession, "Pfam-%s" % database)

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
    def to_jsondict(self):
        json_dict = dict()
        json_dict['accession']   = self.domain.accession
        json_dict['description'] = self.domain.description
        json_dict['identifier']  = self.domain.identifier
        json_dict['mlength']     = self.domain.mlength
        json_dict['p_start']     = self.p_start
        json_dict['p_end']       = self.p_end
        json_dict['s_start']     = self.s_start
        json_dict['s_end']       = self.s_end
        json_dict['perc']        = self.perc
        return json_dict

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

        results = GRAPH.run(query)
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

    def __hash__(self):
        return hash((self.source_symbol, self.target.symbol, self.database, self.parameters['int_prob']))

    def __eq__(self, other):
        return (self.source_symbol, self.target.symbol, self.database, self.parameters['int_prob']) == (other.source_symbol, other.target.symbol, other.database, other.parameters['int_prob'])


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

        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                self.symbol   = row["symbol"]
        else:
            raise NodeNotFound(self.symbol, self.database)

    def get_neighbours(self):
        pass


    def get_homologs(self, database="ALL"):
        """
        Gets all homologs of the specified database. Returns a LIST of Homology objects.
        """
        start_time = time.time()
        # Initialize homologs dictionary
        homologs         = dict()
        database_to_look = set()
        if database == "ALL":
            database_to_look = set(DATABASES)
        else:
            database_to_look = set([database])
        for db in database_to_look:
            homologs[db] = list()

        # Get the homologs
        query = HOMOLOGS_QUERY % (self.symbol)
        results  = GRAPH.run(query)
        results  = results.data()
        if results:
            for row in results:
                database = row['database'][0]
                if database not in database_to_look:
                    continue
                try:
                    homolog_node = PredictedNode(row['homolog'], database, query=False)
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
                homologs[database].append(homolog_rel)
        if homologs:
            return homologs
        else:
            logging.info("NO HOMOLOGS")
            return None

# ------------------------------------------------------------------------------
class WildCard(object):
    """
    Class for wildcard searches. Returns a list of symbols.
    """
    def __init__(self, search, database):
        search = search.upper()
        self.search   = search.replace("*", ".*")
        self.database = database

    def get_symbols(self):
        query   = WILDCARD_QUERY % (self.database, self.search)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            list_of_symbols = list()

            for row in results:
                list_of_symbols.append(row['symbol'])
            return list_of_symbols
        else:
            return list()


# ------------------------------------------------------------------------------
class PredictedNode(Node):
    """
    Class for planarian nodes.
    """
    allowed_databases = DATABASES

    def __init__(self, symbol, database, sequence=None, orf=None, homolog=None, important=False, degree=None, query=True):
        super(PredictedNode, self).__init__(symbol, database)
        self.sequence        = sequence
        self.orf             = orf
        self.homolog         = homolog
        self.important       = important
        self.degree          = degree
        self.gccont          = None
        self.length          = None
        self.orflength       = None
        self.gene_ontologies = list()

        if sequence is None and query is True:
            self.__query_node()

    def get_summary(self):
        '''
        Fills attribute values that are not mandatory, with a summary of several
        features of the node
        '''
        self.length    = len(self.sequence)
        self.orflength = len(self.orf)
        self.gccont = ( self.sequence.count("G") + self.sequence.count("C") ) / self.length

    def __query_node(self):
        "Gets node from neo4j and fills sequence, orf and length attributes."
        query = PREDNODE_QUERY % (self.database, self.symbol)

        results = GRAPH.run(query)
        results = results.data()
        print("ONCE: %s" % self.symbol )

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
            logging.info("NOTFOUND")
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
        if self.homolog is not None:
            element['data']['homolog']  = self.homolog.human.symbol
        if self.degree is not None:
            element['data']['degree']   = self.degree
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
        results = GRAPH.run(query)
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
                    homolog  = thomolog,         degree   = row['tdegree'], query=False
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
        else:
            self.neighbours = None
            self.degree     = 0

        if self.neighbours is not None:
            # Sort interactions by probability
            self.neighbours = sorted(self.neighbours, key=lambda k: k.parameters['int_prob'], reverse=True)
            self.degree     = int(len(self.neighbours))
        return self.neighbours

    def get_expression(self, experiment, sample):
        """
        Gets expression data for a particular node, a particular experiment and a particular sample
        """
        expression = None
        query = EXPRESSION_QUERY % (self.database, self.symbol, experiment.id, sample)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                expression = row["exp"]
        else:
            raise NoExpressionData(self.symbol, self.database, experiment.id, sample)
        return expression

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

    def get_geneontology(self):
        """
        Gets Gene Ontologies of the homologous human protein.
        """
        if self.homolog is None:
            self.__query_node()

        query = GO_HUMAN_GET_GO_QUERY % self.homolog.human.symbol
        results = GRAPH.run(query)
        if results:
            for row in results:
                self.gene_ontologies.append(
                    GeneOntology(accession=row['accession'], domain=row['domain'], query=False)
                )
        else:
            self.gene_ontologies = list()

    def __hash__(self):
        return hash((self.symbol, self.database, self.important))

    def __eq__(self, other):
        return (self.symbol, self.database, self.important) == (other.symbol, other.database, other.important)


# ------------------------------------------------------------------------------
class Experiment(object):
    """
    Class for gene expresssion experiments
    """
    def __init__(self, identifier, url=None, reference=None):
        self.id        = identifier
        self.url         = url
        self.reference   = reference
        self.minexp      = None
        self.maxexp      = None
        self.percentiles = None
        self.gradient    = None
        if self.url is None:
            self.__get_minmax()

    def __get_minmax(self):
        """
        Checks if the specified experiment exists in the database and gets the max and min expression
        ranges defined aswell as the reference.
        """
        query   = EXPERIMENT_QUERY % (self.id)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            self.maxexp      = results[0]["maxexp"]
            self.minexp      = results[0]["minexp"]
            self.reference   = results[0]["reference"]
            self.url         = results[0]["url"]
            self.percentiles = results[0]["percentiles"]


    def to_json(self):
        """
        Returns a json string with the info about the experiment
        """
        json_dict = dict()
        json_dict['id']        = self.id
        json_dict['reference'] = self.reference
        json_dict['url']       = self.url
        json_dict['minexp']    = self.minexp
        json_dict['maxexp']    = self.maxexp
        json_dict['gradient']  = dict()
        for tup in self.gradient:
            json_dict['gradient'][tup[0]] = tup[1]
        return json.dumps(json_dict)

    def color_gradient(self, from_color, to_color, comp_type):
        """
        This method returns a color gradient of length bins from "from_color" to "to_color".
        """
        bins         = list()
        exp_to_color = list()
        range_colors = list()
        s_color = Color(from_color)
        e_color = Color(to_color)
        if comp_type == "one-sample":
            # We assign a color to each percentile
            bins = self.percentiles
            range_colors = list(s_color.range_to(e_color, len(bins)))
            range_colors.reverse()
        else:
            # We assign a color to each number from -10 to +10
            white_starting = Color(from_color)
            white_ending   = Color(to_color)
            white_starting.saturation = 0.1
            white_starting.luminance  = 0.9
            white_ending.saturation = 0.1
            white_ending.luminance  = 0.9
            bins = range(-10,+11)
            half_colors = int(math.ceil(len(bins) / 2.0))
            range_colors.extend(list(s_color.range_to(white_starting, half_colors))[1:half_colors])
            range_colors.append(Color("white"))
            range_colors.extend(list(white_ending.range_to(e_color, half_colors))[1:half_colors])
            range_colors.reverse()
        for i in bins:
            exp_to_color.append((i,  range_colors.pop().get_hex()))
        self.gradient = exp_to_color


# ------------------------------------------------------------------------------
class GraphCytoscape(object):
    """
    Class for a graph object
    """
    def __init__(self):
        self.nodes = set()
        self.edges = set()

    def add_elements(self, elements):
        """
        Method that takes a list of node or PredInteraction objects and adds them
        to the graph.
        """
        for element in elements:
            if isinstance(element, Node):
                self.nodes.add( element )
            elif isinstance(element, PredInteraction):
                self.edges.add( element )
            else:
                raise WrongGraphObject(element)

    def is_empty(self):
        """
        Checks if the graph is empty or not.
        """
        if not self.nodes and not self.edges:
            return True
        else:
            return False

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
        Gets a list/set of nodes and defines them as important
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

    def get_expression(self, experiment, samples):
        """
        Gets the expression for all the node objects in the graph.
        Returns a dictionary: expression_data[node.symbol][sample]
        """
        node_list     = ",".join(map(lambda x: '"' + x + '"', [node.symbol for node in self.nodes ]))
        node_selector = "[" + node_list + "]"
        expression    = dict()
        for sample in samples:
            query = EXPRESSION_QUERY_GRAPH % (node_selector, experiment.id, sample)
            results = GRAPH.run(query)
            results = results.data()
            for row in results:
                if row['symbol'] not in expression:
                    expression[row['symbol']] = dict()
                expression[row['symbol']][sample] = row['exp']
        return expression

    def get_connections(self):
        """
        Function that looks for the edges between the nodes in the graph
        """
        node_q_string = str(list([str(node.symbol) for node in self.nodes]))
        query = GET_CONNECTIONS_QUERY % (node_q_string, node_q_string)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                parameters = dict()
                parameters = {
                    'int_prob'    : round(float(row['int_prob']), 3),
                    'path_length' : round(float(row['path_length']), 3),
                    'cellcom_nto' : round(float(row['cellcom_nto']), 3),
                    'molfun_nto'  : round(float(row['molfun_nto']), 3),
                    'bioproc_nto' : round(float(row['bioproc_nto']), 3),
                    'dom_int_sc'  : round(float(row['dom_int_sc']), 3)
                }
                newinteraction = PredInteraction(
                    database      = row['database'][0],
                    source_symbol = row['nsymbol'],
                    target        = PredictedNode(row['msymbol'], row['database'][0], query=False),
                    parameters    = parameters
                )
                self.add_interaction(newinteraction)

    def __str__(self):
        return self.to_json()

# ------------------------------------------------------------------------------
class ExperimentList(object):
    """
    Maps a list of experiment objects with all its available samples in the DB
    """
    def __init__(self):
        self.experiments = set()
        self.samples     = dict()
        self.datasets    = dict()
        query   = ALL_EXPERIMENTS_QUERY
        # Add all the samples for each experiment
        results = GRAPH.run(query)
        results = results.data()
        added_experiments = set()
        if results:
            for row in results:
                if row['identifier'] not in self.samples:
                    self.samples[ row['identifier'] ] = set()
                self.samples[ row['identifier'] ].update(row['samples'])
                if row['identifier'] not in added_experiments:
                    self.experiments.add(Experiment( row['identifier'], url=row['url'], reference=row['reference'] ))
                    added_experiments.add(row['identifier'])
                if row['identifier'] not in self.datasets:
                    self.datasets[ row['identifier'] ] = set()
                for item in row['datasets']:
                    self.datasets[ row['identifier'] ].update(item)
            for exp in self.samples:
                self.samples[exp] = sorted(self.samples[exp])
            # Sort datasets alphabetically
            for exp in self.datasets:
                self.datasets[exp] = sorted(list(self.datasets[exp]))

    def get_samples(self, experiment):
        """ Returns a set for the given experiment"""
        if experiment in self.samples:
            return self.samples[experiment]
        else:
            raise ExperimentNotFound

    def get_datasets(self, experiment):
        """ Returns a set for the given experiment"""
        if experiment in self.samples:
            return self.datasets[experiment]
        else:
            raise ExperimentNotFound

    def __str__(self):
        final_str = ""
        for exp in self.experiments:
            final_str += "Experiment: %s\n\tsamples: %s\n\tdatasets: %s\n" % (exp, ",".join(self.samples[exp]), ",".join(self.datasets[exp]))
        return final_str

# ------------------------------------------------------------------------------
class GeneOntology(object):
    """
    Class for GeneOntology nodes
    """
    def __init__(self, accession, domain=None, human=False, query=True):
        self.accession   = accession
        self.domain      = domain
        self.human_nodes = list()
        self.go_regexp = r"GO:\d{7}"
        if query is True:
            if self.__check_go() is True:
                if human is True:
                    self.__get_nodes()
                else:
                    self.__query_go()
            else:
                raise NotGOAccession(self)


    def __query_go(self):
        """
        Query DB and get domain
        """
        query   = GO_QUERY % self.accession
        results = GRAPH.run(query)
        results = results.data()
        if results:
            self.domain = results[0]['domain']
        else:
            raise NodeNotFound(self.accession, "Go")

    def __check_go(self):
        """
        Checks if accession is a GO accession
        """
        if re.match(self.go_regexp, self.accession):
            return True
        else:
            return False

    def __get_nodes(self):
        """
        Gets Human nodes symbols with annotated GO
        """
        query   = GO_HUMAN_NODE_QUERY % self.accession
        results = GRAPH.run(query)

        results = results.data()
        if results:
            self.domain = results[0]['domain']
            for row in results:
                self.human_nodes.append(row['symbol'])
        else:
            raise NodeNotFound(self.accession, "Go")


# ------------------------------------------------------------------------------
class Pathway(object):
    """
    Class for pathways. They are basically GraphCytoscape objects with more attributes.
    """
    def __init__(self, graph):
        self.graph = graph
        self.score = 0
        for edge in self.graph.edges:
            self.score += edge.parameters['int_prob']
        self.score = self.score / len(self.graph.edges)

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
        self.symbol   = symbol
        self.database = database
    def __str__(self):
        return "Symbol %s not found in database %s." % (self.symbol, self.database)

# ------------------------------------------------------------------------------
class NoExpressionData(Exception):
    """Exception node has no expression data"""
    def __init__(self, symbol, database, experiment, sample):
        self.symbol     = symbol
        self.database   = database
        self.experiment = experiment
        self.sample     = sample
    def __str__(self):
        return "Expression for experiment %s and sample %s not found for node %s of database %s" % (self.experiment, self.sample, self.symbol, self.database)

# ------------------------------------------------------------------------------
class ExperimentNotFound(Exception):
    """
    Exception thrown when trying to create a experiment object that was not found on the DB
    """
    def __init__(self, experiment):
        self.experiment = experiment
    def __str__(self):
        return "Experiment %s not found in database" % self.experiment

# ------------------------------------------------------------------------------
class SampleNotAvailable(Exception):
    """Exception raised when a specified sample is not found for a particular experiment"""
    def __init__(self, experiment, sample):
        self.experiment = experiment
        self.sample     = sample
    def __str__(self):
        return "Sample %s not found for experiment %s in database" % (self.sample, self.experiment)

# ------------------------------------------------------------------------------
class NotGOAccession(Exception):
    """Exception when GO accession provided to GO object is not a GO accession"""
    def __init__(self, go_object):
        self.go = go_object
    def __str__(self):
        return "GO accession: %s is not an allowed GO accession (GO:\\d{7})" % (self.go.accession)

# ------------------------------------------------------------------------------
class NotPFAMAccession(Exception):
    """Exception when PFAM accession provided to GO object is not a GO accession"""
    def __init__(self, acc):
        self.acc = acc
    def __str__(self):
        return "PFAM accession: %s is not an allowed PFAM accession (PFAM:\\d{7})" % (self.acc)

# ------------------------------------------------------------------------------
class NoHomologFound(Exception):
    """Exception raised when a node homolog is not found. Internal error. Should not happen"""
    def __init__(self, symbol):
        self.symbol = symbol
    def __str__(self):
        return "Homolog of %s not found in database." % (self.symbol)
