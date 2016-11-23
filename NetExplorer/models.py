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
        self.domains    = list()
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

            # Query to get all the relationships between neighbour nodes.
            # Return clause should be changed but it seems to work

            MATCH (n:Cthulhu)-[r:INTERACT_WITH]-(m:Cthulhu)
            WHERE n.symbol = 'cth1_Trc_comp6878_c0_seq1'
            WITH collect(m) as neighbours, n as parent, collect(r) as parentrels
            match (a:Cthulhu)-[l:INTERACT_WITH]-(b:Cthulhu)
            WHERE a in neighbours and b in neighbours
            return a.symbol, b.symbol, l, parentrels, neighbours

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


    def path_to_node(self, target, including=None, excluding=None):
        """
        Given a target node object, this method finds all the shortest paths to that node,
        if there aren't any, it returns None.
        It returns a list of dictionaries, each of them with two keys:
            'nodes': list of PredictedNode objects in path.
            'edges': list of PredInteraction objects in path.
        """
        query = """
            MATCH p=allShortestPaths( (n:%s)-[:INTERACT_WITH*]-(m:%s) )
            WHERE n.symbol = '%s'
            AND m.symbol = '%s'
        """ % (self.database, target.database, self.symbol, target.symbol)
        if including is not None:
            for inc in including:
                query += 'AND ANY(x IN nodes(p) WHERE x.symbol = "%s")\n' % (inc)
        if excluding is not None:
            for exc in excluding:
                query += 'AND NOT ANY(x IN nodes(p) WHERE x.symbol = "%s")\n' % (exc)

        query += "return DISTINCT p"
        print(query)
        results = graph.run(query).data()

        if results:
            paths = list()

            for path in results:
                nodes_obj_in_path = list()
                rels_obj_in_path  = list()
                nodes_in_path     = path['p'].nodes()
                rels_in_path      = path['p'].relationships()
                rel_properties    = None

                for idx, node in enumerate(nodes_in_path):
                    symbol   = node.properties['symbol']
                    sequence = node.properties['sequence']
                    orf      = node.properties['orf']
                    length   = node.properties['length']
                    current_node = PredictedNode(
                                symbol   = symbol,
                                database = self.database,
                                sequence = sequence,
                                orf      = orf,
                                length   = length
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
                paths.append({'nodes': nodes_obj_in_path, 'edges': rels_obj_in_path})
            print(paths)
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
        query = """
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
                """ % (self.database, self.symbol)

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
                domain_annotation = Has_domain(
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
    def __init__(self, prednode, human, blast_cov, blast_eval, nog_brh,  pfam_sc, nog_eval, blast_brh, pfam_brh):
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
class Has_domain(object):
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

    def get_homologs(self, database):
        """
        Gets all homologs of the specified database. Returns a LIST of Homology objects.
        """
        query = """
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
        """ % (database, self.symbol)

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

    def __init__(self, symbol, database, sequence=None, length=None, orf=None):
        super(PredictedNode, self).__init__(symbol, database)
        self.sequence       = None
        self.orf            = None
        self.length         = None
        self.gccont         = None
        self.homolog        = None
        self.n_homologs     = None
        self.n_interactors  = None
        self.homolog_symbol = None
        if sequence is None:
            self.__query_node()

    def __query_node(self):
        "Gets node from neo4j and fills sequence, orf and length attributes."
        query = """
            MATCH (n:%s)-[r:HOMOLOG_OF]-(m:Human)
            WHERE  n.symbol = "%s"
            RETURN n.symbol AS symbol, n.sequence AS sequence, n.orf AS orf, m.symbol AS homolog LIMIT 1
        """ % (self.database, self.symbol)

        results = graph.run(query)
        results = results.data()

        if results:
            for row in results:
                self.symbol         = row["symbol"]
                self.sequence       = row['sequence']
                self.orf            = row["orf"]
                self.homolog_symbol = row['homolog']
        else:
            print("NOTFOUND")
            raise NodeNotFound(self)

    def get_summary(self):
        '''
        Fills attribute values that are not mandatory, with a summary of several
        features of the node
        '''
        self.length = len(self.sequence)
        self.gccont = ( self.sequence.count("G") + self.sequence.count("C") ) / self.length

    def get_homolog(self):
        '''
        Gets human homolog with all its information and saves it as an "homology" object
        in the attribute self.homolog.
        '''
        query = """
            MATCH (n:%s)-[r:HOMOLOG_OF]-(m:Human)
            WHERE  n.symbol = "%s"
            RETURN m.symbol AS human,
                   r.blast_cov AS blast_cov,
                   r.blast_eval AS blast_eval,
                   r.nog_brh AS nog_brh,
                   r.pfam_sc AS pfam_sc,
                   r.nog_eval AS nog_eval,
                   r.blast_brh AS blast_brh,
                   r.pfam_brh AS pfam_brh
        """ % (self.database, self.symbol)

        results = graph.run(query)
        results = results.data()

        if results:
            for row in results:
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
                self.homolog_symbol = human_node.symbol
                return self.homolog

        else:
            return None


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
class NodeNotFound(Exception):
    """Exception raised when a node is not found on the db"""
    def __str__(self):
        return "Symbol %s not found in database %s." % (self.pnode.symbol, self.pnode.database)
