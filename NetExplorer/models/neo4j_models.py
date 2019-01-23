from .common import *

# NEO4J CLASSES
# ------------------------------------------------------------------------------
class Node(object):
    """
    Base class for all the nodes in the database.

    Attributes:
        symbol: String containing the symbol attribute in Neo4j of a given node.
        database: The Label for the symbol in Neo4j.
        neighbours: List of Interaction objects connecting nodes adjacent to the Node.
        domains: HasDomain objects describing domains in the sequence/node. 
        allowed_databases: Class attribute. Set of allowed Labels for Node.
    """

    def __init__(self, symbol, database):
        super(Node, self).__init__()
        self.symbol     = symbol
        self.database   = database.capitalize()
        self.neighbours = list()
        self.domains    = list()
        if self.database not in self.allowed_databases:
            raise exceptions.IncorrectDatabase(self.database)

    def __query_node(self):
        """
        This method will be overriden by HumanNode or PlanarianContig.
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
        query = neoquery.PATH_QUERY % (self.database, plen, target.database, self.symbol, target.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            paths = list()
            for path in results:
                nodes_in_path  = [ PlanarianContig(node, self.database, query=False) for node in path['symbols']]
                relationships  = list()
                path_graph_obj = GraphCytoscape()
                for idx, val in enumerate(path['int_prob']):
                    parameters = dict()
                    parameters['int_prob']    = path['int_prob'][idx]
                    parameters['path_length'] = path['path_length'][idx]
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
        query = neoquery.DOMAIN_QUERY % (self.database, self.symbol)

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
    Class for homology relationships between a PlanarianContig and a HumanNode.

    Attributes:
        prednode: PlanarianContig object.
        human: Human object.
        blast_cov: Float with BLAST coverage value in %.
        blast_eval: Float with BLAST e-value. 
        nog_brh: 1/0 flag indicating if homology is best reciprocal hit in EggNOG alignment.
        nog_eval: Float with EggNOG alignment e-value.
        pfam_sc: Float with pfam meta-alignment score.
        pfam_brh: 1/0 flag indicating if homology is best reciprocal hit in pfam alignment.
    """

    def __init__(self,  human, blast_cov=None, blast_eval=None, nog_brh=None,  pfam_sc=None, nog_eval=None, blast_brh=None, pfam_brh=None, prednode=None):
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
    Class for PFAM domains.

    Attributes:
        accession: String with accession for pfam domain (PFXXXXX).
        description: String with description for pfam domain.
        identifier: String with identifier for pfam domain.
        mlength: Integer with domain length.
    """

    pfam_regexp = r'PF\d{5}'
    def __init__(self, accession, description=None, identifier=None, mlength=None):
        if not re.match(Domain.pfam_regexp, accession):
            raise exceptions.NotPFAMAccession(accession)
        self.accession   = accession
        self.description = description
        self.identifier  = identifier
        self.mlength     = mlength

    @classmethod
    def is_symbol_valid(cls, symbol):
        return re.match(cls.pfam_regexp, symbol)

    def get_planarian_contigs(self, database):
        '''
        Returns a list of PlanarianContigs of 'database'.

        Args:
            database: str, database from which to retrieve the planarian contigs.
        '''
        query = "";
        if not re.match(Domain.pfam_regexp, self.accession):
            # Fuzzy pfam accession (no number)
            acc_regex = self.accession + ".*"
            query = neoquery.DOMAIN_TO_CONTIG_FUZZY % (database, acc_regex)
        else:
            query = neoquery.DOMAIN_TO_CONTIG % (database, self.accession)

        results = GRAPH.run(query)
        results = results.data()
        nodes = list()
        if results:
            for row in results:
                nodes.append(PlanarianContig(row['symbol'], database, query=False))
            return nodes
        else:
            raise exceptions.NodeNotFound(self.accession, "Pfam-%s" % database)

    
# ------------------------------------------------------------------------------
class HasDomain(object):
    """
    Class for relationships between a node and a Pfam domain annotated on the sequence.

    Attributes:
        domain: Domain object.
        node: Node object.
        p_start: integer describing the start coordinate (1-indexed) on the PFAM domain.
        p_end: integer describing the end coordinate (1-indexed) on the PFAM domain.
        s_start: integer describing the start coordinate (1-indexed) on the sequence.
        s_end: integer describing the end coordinate (1-indexed) on the sequence.
        perc: float with % of domain in sequence.

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
    Source and target are PlanarianContig attributes.

    Attributes:
        source_symbol: Symbol of parent node of interaction.
        target: Node object of the child node of the interaction.
        database: Neo4j label of parent and child nodes.
        parameters: Dictionary containing the interaction properties.
                    {'int_prob', 'path_length', 
                    'cellcom_nto', 'molfun_nto', 
                    'bioproc_nto', 'dom_int_sc'}
    """

    def __init__(self, source_symbol, target, database, parameters=None, query=True):
        self.source_symbol = source_symbol
        self.target        = target
        self.database      = database
        self.parameters    = parameters
        if query is True and self.parameters is None:
            self.__query_interaction()

    def __query_interaction(self):
        """
        This private method will fetch the interaction from the DB.
        """
        query = neoquery.PREDINTERACTION_QUERY % (self.database, self.database, self.source_symbol, self.target.symbol)

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
        if self.parameters is not None:
            element['data']['pathlength']  = self.parameters['path_length']
            element['data']['probability'] = self.parameters['int_prob']

            if self.parameters['path_length'] == 1:
                element['data']['colorEDGE']   = "#72a555"
            else:
                element['data']['colorEDGE']   = "#CA6347"
        else:
            element['data']['colorEDGE']   = "#CA6347"

        return element

    def __hash__(self):
        return hash((self.source_symbol, self.target.symbol, self.database))

    def __eq__(self, other):
        return (self.source_symbol, self.target.symbol, self.database) == (other.source_symbol, other.target.symbol, other.database)


# ------------------------------------------------------------------------------
class HumanNode(Node):
    """
    Human node class definition. Inherits from 'Node'.

    Attributes:
        summary: String with gene summary.
        summary_source: String with the source of the summary.
    """

    allowed_databases = set(["Human"])

    def __init__(self, symbol, database, query=True):
        super(HumanNode, self).__init__(symbol, database)
        if query is True:
            self.__query_node()
        self.summary = None
        self.summary_source = None

    def __query_node(self):
        query = neoquery.HUMANNODE_QUERY % (self.database, self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                self.symbol   = row["symbol"]
        else:
            raise exceptions.NodeNotFound(self.symbol, self.database)

    def get_neighbours(self):
        pass

    def to_jsondict(self):
        element                     = dict()
        element['data']             = dict()
        element['data']['id']       = self.symbol
        element['data']['name']     = self.symbol
        element['data']['database'] = self.database
        return element

    def get_planarian_genes(self, database):
        '''
        Gets planarian gene objects (PlanarianGene) connected to HumanNode
        through contigs of dataset 'database', e.g.: (Human)->(Dresden)->(Smesgene)

        Args:
            database: string, database of contigs to get PlanarianGene
        '''
        query = neoquery.GET_GENES_FROMHUMAN_QUERY % (database, self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            smesgenes = list()
            for row in results:
                smesgene = PlanarianGene(
                    row['symbol'], 
                    'Smesgene', 
                    name=row['name'], 
                    start=row['start'], 
                    end=row['end'], 
                    strand=row['strand'], 
                    sequence=row['sequence'],
                    query=False
                )
                homology = Homology(
                    prednode   = PlanarianContig(row['prednode_symbol'], database, query=False),
                    human      = self,
                    blast_cov  = row['blast_cov'],
                    blast_eval = row['blast_eval'],
                    nog_brh    = row['nog_brh'],
                    pfam_sc    = row['pfam_sc'],
                    nog_eval   = row['nog_eval'],
                    blast_brh  = row['blast_brh'],
                    pfam_brh   = row['pfam_brh']
                )
                smesgene.homolog = homology
                smesgenes.append(smesgene)
            return smesgenes
        else:
            return list()


    def get_summary(self):
        """
        Retrieves gene summary when available
        """
        query = neoquery.SUMMARY_QUERY % (self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            self.summary = results[0]['summary']
            self.summary_source = results[0]['summary_source']
        else:
            self.summary = "NA"
            self.summary_source = "NA"
        return self            

    def get_planarian_contigs(self, database):
        '''
        Gets all PlanarianContigs homologous to HumanNode.

        Args:
            database: str, Database from which to retrieve planarian contigs.

        Returns:
            list: PlanarianContigs objects.
        '''
        homologs = self.get_homologs(database)
        planarian_contigs = list()
        for db, homologies in homologs.items():
            for homology in homologies:
                planarian_contigs.append(homology.prednode)
        return planarian_contigs

    def get_homologs(self, database="ALL"):
        """
        Gets all homologs of the specified database. Returns a dictionary of the form:
            dict['database'] = [ Homology() ]

        Returns:
            dictionary: key='database', value=List of Homology objects.
        """
        # Initialize homologs dictionary
        homologs         = dict()
        database_to_look = set()
        query_to_use = neoquery.HOMOLOGS_QUERY
        if database == "ALL":
            database_to_look = set(DATABASES)
            query_to_use = neoquery.HOMOLOGS_QUERY_ALL % (self.symbol)
        else:
            database_to_look = set([database])
            query_to_use = neoquery.HOMOLOGS_QUERY % (database, self.symbol)
        for db in database_to_look:
            homologs[db] = list()

        # Get the homologs
        results  = GRAPH.run(query_to_use)
        results  = results.data()
        if results:
            for row in results:
                database = row['database'][0]
                if database not in database_to_look:
                    continue
                try:
                    homolog_node = PlanarianContig(row['homolog'], database, query=False)
                    homolog_node.get_gene_name()
                except Exception as err:
                    continue
                homolog_rel    = Homology(
                    prednode   = homolog_node,
                    human      = self,
                    blast_cov  = row['blast_cov'],
                    blast_eval = row['blast_eval'],
                    nog_brh    = row['nog_brh'],
                    pfam_sc    = row['pfam_sc'],
                    nog_eval   = row['nog_eval'],
                    blast_brh  = row['blast_brh'],
                    pfam_brh   = row['pfam_brh']
                )
                homolog_node.homolog = homolog_rel
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

    Attributes:
        search: String to search.
        database: Database (label in neo4j) for the search.
    """
    def __init__(self, search, database):
        search = search.upper()
        self.search   = search.replace("*", ".*")
        self.database = database

    def get_human_genes(self):
        '''
        Returns list of HumanNode objects matching the wildcard query.

        Returns:
            list: HumanNode objects.
        '''
        query   = neoquery.SYMBOL_WILDCARD % (self.database, self.search)
        results = GRAPH.run(query)
        results = results.data()
        list_of_nodes = list()
        if results:
            for row in results:
                list_of_nodes.append(HumanNode(row['symbol'], "Human", query=False))
        return list_of_nodes

    def get_planarian_genes(self):
        '''
        Returns list of PlanarianGene objects matching the wildcard query.
        '''
        query = neoquery.NAME_WILDCARD % (self.database, self.search)
        results = GRAPH.run(query)
        results = results.data()
        list_of_nodes = list()
        if results:
            for row in results:
                list_of_nodes.append(PlanarianGene(row['symbol'], "Smesgene", name=row['name'], query=False))
        return list_of_nodes


# ------------------------------------------------------------------------------
class PlanarianContig(Node):
    """
    Class for planarian nodes.

    Attributes:
        symbol: String with Node symbol.
        database: String with label for Neo4j.
        homolog: 'Homology' object with human homolog gene.
        important: Bool indicating if Node should be marked on graph visualization.
        degree: Integer with the degree (number of connections) of the node.
        allowed_databases: Class attribute, dictionary with names of neo4j 
            labels for planarian genes.
    """
    allowed_databases = ALL_DATABASES

    def __init__(self, symbol, database,
                 sequence=None, name=None, gene=None,
                 orf=None, homolog=None, important=False,
                 degree=None, query=True):
        super(PlanarianContig, self).__init__(symbol, database)
        self.sequence = sequence
        self.orf = orf
        self.homolog = homolog
        self.important = important
        self.degree = degree
        self.gccont = None
        self.length = None
        self.orflength = None
        self.gene_ontologies = list()
        self.name = name
        self.gene = gene

        if sequence is None and query is True:
            self.__query_node()
            self.get_gene_name()

    def get_gene_name(self):
        '''
        Gets gene name if possible
        '''
        if self.gene is None:
            query = neoquery.GET_GENE % (self.database, self.symbol)
            results = GRAPH.run(query)
            results = results.data()
            if results:
                self.gene = results[0]['genesymbol']
                if results[0]['name']:
                    self.name = results[0]['name']
            else:
                self.gene = None
                self.name = None

    def get_genes(self):
        '''
        Gets Genes to which this contig maps.
        '''
        query = neoquery.GET_GENES_QUERY % (self.database, self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            return [ 
                PlanarianGene(
                    res['symbol'], 
                    'Smesgene', 
                    name=res['name'], 
                    start=res['start'], 
                    end=res['end'], 
                    strand=res['strand'], 
                    sequence=res['sequence'],
                    query=False
                ) 
                for res in results
            ]
        else:
            return list()


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
        query = neoquery.PREDNODE_QUERY % (self.database, self.symbol)

        results = GRAPH.run(query)
        results = results.data()

        if results:
            for row in results:
                # Add node
                self.symbol         = row["symbol"]
                self.sequence       = row['sequence']
                self.orf            = row["orf"]
                self.length         = row['length']

                # Add homolog
                human_node = HumanNode(row['human'], "Human", query=False)
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
            # Maybe node does not have an homolog
            query = neoquery.PREDNODE_NOHOMOLOG_QUERY % (self.database, self.symbol)
            results = GRAPH.run(query)
            results = results.data()

            if results:
                self.symbol = results[0]['symbol']
                self.sequence = results[0]['sequence']
                self.orf = results[0]['orf']
                self.length = results[0]['length']
                self.homolog = None
            else:
                raise exceptions.NodeNotFound(self.symbol, self.database)

    def get_all_information(self):
        '''
        Fills all attributes of PlanarianContig by querying the database
        '''
        self.__query_node()

    def get_homolog(self):
        '''
        Tries to get the homologous human gene of this planarian transcript
        '''
        self.__query_node()

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
            element['data']['colorNODE'] = "#404040"
            element['classes'] = 'important'
        else:
            element['data']['colorNODE'] = "#404040"
        return element

    def get_neighbours_shallow(self):
        '''
        Method to get adjacent nodes (and their degree) in the graph without 
        homology information and only with path_length and probability for the interaction information.
        It also retrieves the degree of the neighbour nodes.
        Fills attribute neighbours, which will be a list of PredInteraction objects.
        Used by NetExplorer add_connection/expand
        '''
        query = neoquery.NEIGHBOURS_QUERY_SHALLOW % (self.database, self.database, self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                parameters = dict()
                # Homology object
                human_node = HumanNode(row['human'], "Human", query=False)
                thomolog  = Homology(human = human_node)
                # Node Object
                target = PlanarianContig(
                    symbol   = row['target'],    database = self.database,
                    homolog  = thomolog,         degree = row['tdegree'],
                    query=False
                )

                # Add prednode to homology object
                target.homolog.prednode = target

                # Interaction Object
                interaction = PredInteraction(
                    source_symbol = self.symbol,
                    target        = target,
                    database      = self.database,
                    query         = False,
                    parameters    = { 
                        'path_length': int(row['path_length']), 
                        'int_prob': round(float(row['int_prob']), 3)
                    } 
                )
                # Add interaction to list of neighbours
                self.neighbours.append(interaction)
        else:
            self.neighbours = None
            self.degree     = 0
        return self.neighbours

    def get_neighbours(self):
        """
        Method to get the adjacent nodes in the graph and all the information about 
        those connections (including the homology information, etc.).
        Fills attribute neighbours, which will be a list of PredInteraction objects.
        """
        query = neoquery.NEIGHBOURS_QUERY % (self.database, self.database, self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                parameters = dict()
                # Initialize parameters to pass to the PredInteraction object
                parameters = {
                    'int_prob'    : round(float(row['int_prob']), 3),
                    'path_length' : int(row['path_length']),
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
                target = PlanarianContig(
                    symbol   = row['target'],    database = self.database,
                    homolog  = thomolog,         query=False
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
        query = neoquery.EXPRESSION_QUERY % (self.database, self.symbol, experiment.id, sample)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            for row in results:
                expression = row["exp"]
        else:
            raise exceptions.NoExpressionData(self.symbol, self.database, experiment.id, sample)
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
        if self.neighbours:
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
        
        if self.homolog is not None:
            
            query = neoquery.GO_HUMAN_GET_GO_QUERY % self.homolog.human.symbol
            results = GRAPH.run(query)
            if results:
                for row in results:
                    self.gene_ontologies.append(
                        GeneOntology(accession=row['accession'], domain=row['domain'], name=row['name'], query=False)
                    )
            else:
                self.gene_ontologies = list()
        else:
            self.gene_ontologies = list()

    def __hash__(self):
        return hash((self.symbol, self.database, self.important))

    def __eq__(self, other):
        return (self.symbol, self.database, self.important) == (other.symbol, other.database, other.important)


# ------------------------------------------------------------------------------
class oldExperiment(object):
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
        query   = neoquery.EXPERIMENT_QUERY % (self.id)
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
                raise exceptions.WrongGraphObject(element)

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
            query = neoquery.EXPRESSION_QUERY_GRAPH % (node_selector, experiment.id, sample)
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
        query = neoquery.GET_CONNECTIONS_QUERY % (node_q_string, node_q_string)
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
                    target        = PlanarianContig(row['msymbol'], row['database'][0], query=False),
                    parameters    = parameters
                )
                self.add_interaction(newinteraction)

    def new_nodes(self, symbols, database):
        """
        Takes a list of symbols and returns the necessary GraphCytoscape with Human or PlanarianContig objects

        Args:
            symbols: List of strings with gene/contig/pfam/go/kegg symbols.
            database: String with database.
        """
        for symbol in symbols:
            symbol = symbol.replace(" ", "")
            symbol = symbol.replace("'", "")
            symbol = symbol.replace('"', '')
            node_objects = list()
            try:
                gene_search = GeneSearch(symbol, database)

                if database == "Human":
                    node_objects = gene_search.get_human_genes()
                elif database == "Smesgene":
                    node_objects = gene_search.get_planarian_genes()
                else:
                    node_objects = gene_search.get_planarian_contigs()
                self.add_elements(node_objects)
            except exceptions.NodeNotFound:
                continue
            

    def __str__(self):
        return self.to_json()

    def __bool__(self):
        if self.nodes:
            return True
        else:
            return False
    __nonzero__=__bool__

# ------------------------------------------------------------------------------
class ExperimentList(object):
    """
    Maps a list of experiment objects with all its available samples in the DB
    """
    def __init__(self, user):
        self.experiments = set()
        self.samples     = dict()
        self.datasets    = dict()
        query   = neoquery.ALL_EXPERIMENTS_QUERY
        # Add all the samples for each experiment
        results = GRAPH.run(query)
        results = results.data()
        added_experiments = set()

        # Check if user is authenticated to get private experiments
        access_to = set()
        if user.is_authenticated:
            try:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT auth_user.username, user_exp_permissions.experiment
                    FROM auth_user
                    INNER JOIN user_exp_permissions ON auth_user.id=user_exp_permissions.user_id
                    WHERE auth_user.username = %s;
                ''', [user.username])
                rows = cursor.fetchall()
                access_to.update([row[1] for row in rows])
            except Exception:
                pass

        if results:
            for row in results:
                if row['identifier'] not in self.samples:
                    self.samples[ row['identifier'] ] = set()
                self.samples[ row['identifier'] ].update(row['samples'])
                if row['identifier'] not in added_experiments:
                    if row['private'] == 1:
                        if row['identifier'] not in access_to:
                            continue
                    self.experiments.add(oldExperiment( row['identifier'], url=row['url'], reference=row['reference'] ))
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
            raise exceptions.ExperimentNotFound

    def get_datasets(self, experiment):
        """ Returns a set for the given experiment"""
        if experiment in self.samples:
            return self.datasets[experiment]
        else:
            raise exceptions.ExperimentNotFound

    def __str__(self):
        final_str = ""
        for exp in self.experiments:
            final_str += "Experiment: %s\n\tsamples: %s\n\tdatasets: %s\n" % (exp, ",".join(self.samples[exp]), ",".join(self.datasets[exp]))
        return final_str


# ------------------------------------------------------------------------------
class KeggPathway(object):
    '''
    Class for KeggPathways
    '''
    def __init__(self, symbol, database):
        self.symbol = symbol
        self.database = database
        self.kegg_url = "http://togows.dbcls.jp/entry/pathway/%s/genes.json" % symbol
        self.graphelements = self.connect_to_kegg()

    def connect_to_kegg(self):
        '''
        Connects to KEGG and extracts the elements of the pathway
        '''
        r = requests.get(self.kegg_url)
        if r.status_code == 200:
            if r.json():
                gene_list = [gene.split(";")[0] for gene in r.json()[0].values()]
                graphelements = GraphCytoscape()
                graphelements.new_nodes(gene_list, self.database)
                graphelements.get_connections()
                return graphelements
            else:
                return GraphCytoscape()
        else:
            return GraphCytoscape()

    def is_empty(self):
        '''
        Checks if the KeggPathway is empty
        '''
        return self.graphelements.is_empty()
                
# ------------------------------------------------------------------------------
class GeneOntology(object):
    """
    Class for GeneOntology nodes
    """
    go_regexp = r"GO:\d{7}"

    def __init__(self, accession, domain=None, name=None, human=False, query=True):
        self.accession = accession
        self.domain = domain
        self.name = name
        self.human_nodes = list()
        if query is True:
            if GeneOntology.is_symbol_valid(self.accession):
                if human is True:
                    self.get_human_genes()
                else:
                    self.__query_go()
            else:
                raise exceptions.NotGOAccession(self)

    @classmethod
    def is_symbol_valid(cls, symbol):
        return re.match(cls.go_regexp, symbol)

    def __query_go(self):
        """
        Query DB and get domain
        """
        query   = neoquery.GO_QUERY % self.accession
        results = GRAPH.run(query)
        results = results.data()
        if results:
            self.domain = results[0]['domain']
            self.name   = results[0]['name']
        else:
            raise exceptions.NodeNotFound(self.accession, "Go")

    def get_human_genes(self):
        """
        Gets Human nodes symbols with annotated GO
        """
        query   = neoquery.GO_HUMAN_NODE_QUERY % self.accession
        results = GRAPH.run(query)

        results = results.data()
        if results:
            self.domain = results[0]['domain']
            for row in results:
                self.human_nodes.append(HumanNode(row['symbol'], "Human", query=False))
        else:
            raise exceptions.NodeNotFound(self.accession, "Go")
        return self.human_nodes

    def get_planarian_contigs(self, database):
        """
        Gets planarian contigs whose homolog has the GO annotated. (GO)<-(Human)<-(Contig)

        Args:
            database: str, database string from which to retrieve the PlanarianContigs.

        Returns:
            list: List of PlanarianContig objects.
        """
        query = neoquery.GO_TO_CONTIG % (database, self.accession)
        results = GRAPH.run(query)
        results = results.data()
        contigs = list()
        if results:
            for data in results:
                contig = PlanarianContig(
                    data['symbol'], 
                    database, 
                    query=False)
                contig.homolog = Homology(
                    prednode   = contig,
                    human      = HumanNode(data['human'], "Human", query=False),
                    blast_cov  = data['blast_cov'],
                    blast_eval = data['blast_eval'],
                    nog_brh    = data['nog_brh'],
                    pfam_sc    = data['pfam_sc'],
                    nog_eval   = data['nog_eval'],
                    blast_brh  = data['blast_brh'],
                    pfam_brh   = data['pfam_brh']
                )
                contigs.append(contig)
        return contigs


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


# ------------------------------------------------------------------------------
class GeneSearch(object):
    """
    Class for node/gene searches

    Attributes:
        sterm: string, term to search.
        database: string, database to search for sterm.
        sterm_database: string, database to which sterm belongs to.
    """

    def __init__(self, sterm, database):
        '''
        Constructor for GeneSearch.

        Args:
            sterm: string, search term.
            database: string, database string to search for sterm.
        '''
        self.sterm = sterm
        self.database = database
        self.sterm_database = None
    
    def infer_symbol_database(self):
        '''
        Compares the symbol in self.sterm to the valid
        patterns for each NodeType.
        '''
        datasets = Dataset.objects.all()
        for dataset in datasets:
            if dataset.is_symbol_valid(self.sterm):
                self.sterm_database = dataset.name
        if self.sterm_database is None:
            # Not valid for any database.
            # Check Smesgene, PFAM, GO, Human in that order.
            if PlanarianGene.is_symbol_valid(self.sterm):
                self.sterm_database = "Smesgene"
            elif Domain.is_symbol_valid(self.sterm):
                self.sterm_database = "PFAM"
            elif GeneOntology.is_symbol_valid(self.sterm):
                self.sterm_database = "GO"
            else:
                self.sterm_database = "Human"
    
    def get_planarian_contigs(self):
        '''
        Returns PlanarianContig objects independently of the search term used.
        '''
        if self.sterm_database is None:
            self.infer_symbol_database()

        planarian_contigs = list()
        source_nodes = list()
        if self.sterm_database == "Smesgene":
            source_nodes.append(PlanarianGene(self.sterm, self.sterm_database))
        elif self.sterm_database == "PFAM":
            source_nodes.append(Domain(self.sterm))
        elif self.sterm_database == "GO":
            source_nodes.append(GeneOntology(self.sterm))
        elif self.sterm_database == "Human" :
            if "*" in self.sterm:
                source_nodes = WildCard(self.sterm, self.sterm_database).get_human_genes()
            else:
                source_nodes = [ HumanNode(self.sterm.upper(), self.sterm_database) ]
        else:
            # We already have the planarian contig by identifier,
            # no need to try to retrieve it from neo4j connections.
            planarian_contigs =  [ PlanarianContig(self.sterm, self.sterm_database) ]
            return planarian_contigs

        for snode in source_nodes:
            planarian_contigs.extend(snode.get_planarian_contigs(self.database))

        for pcontig in planarian_contigs:
            if not pcontig.homolog:
                pcontig.get_homolog()
            if not pcontig.name:
                pcontig.get_gene_name()
        return planarian_contigs

    def get_planarian_genes(self):
        '''
        Returns PlanarianGene object from search term.
        '''
        if self.sterm_database is None:
            self.infer_symbol_database()
        planarian_genes = list()
        
        if self.sterm_database == "Human":
            if "*" in self.sterm:
                human_nodes = WildCard(self.sterm, self.sterm_database).get_human_genes()
            else:
                human_nodes = [ HumanNode(self.sterm.upper(), self.sterm_database) ]
            for hnode in human_nodes:
                planarian_genes.extend(hnode.get_planarian_genes(PlanarianGene.preferred_database))
        elif self.sterm_database == "PFAM":
            planarian_nodes = Domain(self.sterm).get_planarian_contigs(PlanarianGene.preferred_database)
            for contig in planarian_nodes:
                planarian_genes.extend(contig.get_genes())
        elif self.sterm_database == "Smesgene":
            planarian_genes.append(PlanarianGene(self.sterm, self.sterm_database))
        elif self.sterm_database == "GO":
            pass
        else:
            # Transcriptome database
            planarian_node = PlanarianContig(self.sterm, self.sterm_database)
            planarian_genes.extend(planarian_node.get_genes())

        for pgene in planarian_genes:
            if not pgene.homolog:
                pgene.get_homolog()
        planarian_genes = list(set(planarian_genes)) # Unique genes only 
        return planarian_genes

    def get_human_genes(self):
        '''
        Returns HumanNode objects indepdendently of the search term used.
        '''
        if self.sterm_database is None:
            self.infer_symbol_database()

        human_nodes = list()
        if self.sterm_database == "Human":
            if "*" in self.sterm:
                human_nodes = WildCard(self.sterm, self.sterm_database).get_human_genes()
            else:
                human_nodes = [ HumanNode(self.sterm.upper(), self.sterm_database) ]
        elif self.sterm_database == "GO":
            human_nodes = GeneOntology(self.sterm, human=True).human_nodes
        return human_nodes


class PlanarianGene(Node):
    """
    Class for PlanarianGenes (genes from Planmine 3.0 gene annotation)
    """
    smesgene_regexp = r'SMESG\d+'
    preferred_database = "Smest"
    allowed_databases = set(["Smesgene"])

    def __init__(self, symbol, database, 
                 name=None, start=None, end=None, 
                 strand=None, sequence=None, homolog=None, 
                 chromosome=None, query=True):
        super(PlanarianGene, self).__init__(symbol, database)
        self.name = name
        self.start = start
        self.end = end
        self.strand = strand
        self.sequence = sequence
        self.chromosome = chromosome
        self.homolog = homolog

        if sequence is None and query is True:
            self.__query_node()
            self.get_homolog()

    @classmethod
    def is_symbol_valid(cls, symbol):
        '''
        Checks if symbol is valid

        Args:
            symbol: string, symbol to check if follows PlanarianGene naming convention.
        '''
        return re.match(cls.smesgene_regexp, symbol.upper())

    def __query_node(self):
        '''
        Queries PlanarianGene to get the attributes from the database.
        '''
        query = neoquery.SMESGENE_QUERY % (self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        if results:
            self.name = results[0]['name']
            self.sequence = results[0]['sequence']
            self.chromosome = results[0]['chromosome']
            self.strand = results[0]['strand']

            self.start = int(results[0]['start'])
            self.end = int(results[0]['end'])
            
            # Add 2000 nts for good visualization
            self.start -= 5000
            self.end += 5000
        else:
            raise exceptions.NodeNotFound(self.symbol, self.database)


    def get_homolog(self):
        '''
        Gets homologous gene of longest transcript associated with this PlanarianGene.
        Fills attribute 'homolog'. Returns the HumanNode object.
        '''
        best_transcript = self.get_best_transcript()
        if best_transcript:
            best_transcript.get_homolog()
            if best_transcript.homolog:
                self.homolog = best_transcript.homolog
            else:
                self.homolog = None
            return self.homolog
        else:
            return None


    def get_best_transcript(self):
        '''
        Retrieves the longest transcript of preferred_database.
        '''
        best = self.get_planarian_contigs(PlanarianGene.preferred_database)
        if best:
            best = best[0]
        else:
            best = None
        return best


    def get_planarian_contigs(self, database=None):
        '''
        Returns list PlanarianContig objects of database or all databases that map to
        the PlanarianGene genomic location.
        
        Args:
            database: string, optional, database from which to retrieve planarian contigs.
                      if not defined will get all planarian contigs.

        Returns:
            list: PlanarianContig objects.
        '''
        if database is None:
            query = neoquery.SMESGENE_GET_ALL_CONTIGS_QUERY % (self.symbol)
        else:
            query = neoquery.SMESGENE_GET_CONTIGS_QUERY % (database, self.symbol)
        results = GRAPH.run(query)
        results = results.data()
        prednodes = list()
        if results:
            for contig in results:
                if 'database' in contig:
                    database = contig['database'][0]
                prednode = PlanarianContig(contig['symbol'], database, query=False)
                prednode.length = contig['length']
                prednodes.append(prednode)
        else:
            symbol_err = "Transcripts of %s" % self.symbol
            if database is None:
                database = "All"
            raise exceptions.NodeNotFound(symbol_err, database)
        return prednodes

    def __hash__(self):
        return hash((self.symbol))

    def __eq__(self, other):
        return self.symbol == other.symbol


# To avoid import errors
from NetExplorer.models.mysql_models import *
from NetExplorer.models import neo4j_queries as neoquery
from NetExplorer.models import exceptions