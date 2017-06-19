"""
Views of PlanNet
"""

from django.shortcuts   import render
from django.shortcuts   import render_to_response
from django.http        import HttpResponse
from django.template    import RequestContext
from NetExplorer.models import *
from subprocess import Popen, PIPE, STDOUT
from django.contrib.staticfiles.templatetags.staticfiles import static
import tempfile
import textwrap
import json
import re
import logging
import math
import time
import requests

# -----------------------
# CONSTANTS
# -----------------------
BLAST_DB_DIR    = "/home/compgen/scastillo/PlanNET/blast/"
MAX_NUMSEQ      = 50
MAX_CHAR_LENGTH = 25000


# -----------------------
# FUNCTIONS
# -----------------------

def query_node(symbol, database):
    '''
    This simple function takes a symbol and a database and tries to get it from
    the DB
    '''
    node   = None
    symbol = symbol.replace(" ", "")
    symbol = symbol.replace("'", "")
    symbol = symbol.replace('"', '')
    symbol = symbol.replace("%7C", "|")
        # Urls in django templates are double encoded for some reason
        # Because we have identifiers with '|' symbols, they get encoded to %257, that gets decodeed
        # to %7C. I have to re-decode it to '|'

    if database == "Human":
        symbol = symbol.upper()
        node = HumanNode(symbol, database)
    else:
        node = PredictedNode(symbol, database)
        node.get_summary()
    return node

# ------------------------------------------------------------------------------
def symbol_is_empty(symbol):
    '''
    Checks if the input symbol from the forms is empty or not
    '''
    if re.match(r"[a-zA-Z0-9]", symbol):
        return False
    else:
        return True

# ------------------------------------------------------------------------------
def get_shortest_paths(startnodes, endnodes, plen):
    '''
    This function gets all the possible shortest paths between the specified nodes.
    Returns a json string with all the nodes and edges, the length of the paths and
    the total number of paths
    '''
    graphelements = list()
    numpath = 0
    for snode in startnodes:
        for enode in endnodes:
            paths = snode.path_to_node(enode, plen)
            if paths is None:
                # Return no-path that matches the query_node
                continue
            else:
                for path in paths:
                    graphelements.append( GraphCytoscape() )
                    graphelements[numpath].add_elements(path.graph.nodes)
                    graphelements[numpath].add_elements(path.graph.edges)
                    graphelements[numpath] = (graphelements[numpath].to_json, round(path.score, 2))
                    numpath += 1
    return graphelements, numpath

# ------------------------------------------------------------------------------
def substitute_human_symbols(symbols, database):
    """
    This function will get a list of symbols and it will substitute all human symbols by
    the "homologs" of the specified database. It will return the "new" list of symbols
    """
    symbol_regexp = {
        "Cthulhu":      r"cth1_",
        "Consolidated": r"OX_Smed",
        "Dresden":      r"dd_Smed",
        "Graveley":     r"CUFF\.\d+\.\d+",
        "Newmark":      r"Contig\d+",
        "Illuminaplus": r"Gene_\d+_.+",
        "Adamidi":      r"contig\d+|isotig\d+",
        "Blythe":       r"AAA\.454ESTABI\.\d+",
        "Pearson":      r"BPKG\d+",
        "Smed454":      r"90e_\d+|gnl\|UG\|Sme#S\d+/"
    }
    go_regexp   = r"GO:\d{7}"
    pfam_regexp = r'PF\d{5}'
    newsymbols = list()

    for symbol in symbols:
        symbol = symbol.replace(" ", "")
        symbol = symbol.replace("'", "")
        symbol = symbol.replace('"', '')
        if re.match(symbol_regexp[database], symbol):
            newsymbols.append(symbol)
        else:
            wildcard_symbols = list()
            if (re.match(go_regexp, symbol)):
                # GO
                try:
                    wildcard_symbols.extend(GeneOntology(symbol, human=True).human_nodes)
                except (NodeNotFound):
                    continue
            elif (re.match(pfam_regexp, symbol)):
                # PFAM
                domain = Domain(accession=symbol)
                try:
                    newsymbols.extend(domain.get_nodes(database))
                except (NodeNotFound):
                    continue
            else:
                # MUST BE HUMAN
                try:
                    wildcard_symbols.extend( substitue_wildcards([symbol]) )
                except Exception as err:
                    continue
            for final_symbol in wildcard_symbols:
                try:
                    symbol = final_symbol.upper()
                    human_node = HumanNode(symbol, "Human")
                    homologs   = human_node.get_homologs(database)
                    for db in homologs:
                        for hom in homologs[db]:
                            newsymbols.append(hom.prednode.symbol)
                except (NodeNotFound, IncorrectDatabase):
                    # Node is not a human node :_(
                    logging.info("ERROR: NodeNotFound or IncorrectDatabase in substitute_human_symbols")
                    continue
            logging.info("SEARCH INFO: %s does not match %s" %(symbol, symbol_regexp[database]))
    return newsymbols

# ------------------------------------------------------------------------------
def get_subgraph(nodes_including, databases):
    """
    Function that gets a list of nodes and datbases and returns a graph in json format ready to be
    returned to netexplorer
    """
    graph           = GraphCytoscape()
    for node_id, database in zip(nodes_including, databases):
        try:
            node = query_node(node_id, database)
            nodes, edges = node.get_graphelements()
            graph.add_elements(nodes)
            graph.add_elements(edges)
        except NodeNotFound:
            # Requested node not in DB, go on
            continue
    graph.filter( set(nodes_including) )
    graphelements = graph.to_json()
    return graphelements


# ------------------------------------------------------------------------------
def substitue_wildcards(symbols):
    """
    Gets a list of human symbols and returns another list of human symbols that match the specified REGEX.
    """
    wildcard_symbols = list()
    for symbol in symbols:
        if "*" in symbol:
            wildcard_symbols.extend( WildCard(symbol, "Human").get_symbols() )
        else:
            wildcard_symbols.append(symbol)
    return wildcard_symbols

# -----------------------
# VIEWS
# -----------------------

# ------------------------------------------------------------------------------
def index_view(request):
    '''
    This is the first view the user sees.
    It contains the forms, a mini-tutorial, etc.
    And links to all the functions.
    '''

    return render(request, 'NetExplorer/index.html')

# ------------------------------------------------------------------------------
def get_fasta(request):
    '''
    This function will serve FASTA files
    '''

    genesymbol   = request.GET['genesymbol']
    typeseq      = request.GET['type']
    if "database" in request.GET:
        database = request.GET['database']
    else:
        pass # server error!!

    node = None
    try:
        node = query_node(genesymbol, database)
    except (NodeNotFound, IncorrectDatabase):
        pass # server error!

    sequence = str()
    filename = "%s" % node.symbol
    if typeseq == "sequence":
        sequence = textwrap.fill(node.sequence, 70)
        filename = filename + ".fa"
    elif typeseq == "orf":
        sequence = textwrap.fill(node.orf, 70)
        filename = filename + "-orf.fa"

    sequence = ">%s\n" % node.symbol + sequence
    response = HttpResponse(sequence, content_type='text/plain; charset=utf8')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


# ------------------------------------------------------------------------------
def get_card(request, symbol=None, database=None):
    """
    Function that gets a gene id and a database and returns the HTML of the card.
    """
    if request.method == 'GET' and request.is_ajax():
        symbol    = request.GET['target']
        database  = request.GET['targetDB']

    try:
        card_node    = query_node(symbol, database)
        if database != "Human":
            card_node.get_domains()
            card_node.get_geneontology()
            nodes, edges = card_node.get_graphelements()
            graph        = GraphCytoscape()
            graph.add_elements(nodes)
            graph.add_elements(edges)
        else:
            homologs = card_node.get_homologs()
    except (NodeNotFound, IncorrectDatabase):
        return render_to_response('NetExplorer/not_interactome.html')

    if database != "Human":
        response = {
            'node'      : card_node,
            'json_graph': graph.to_json(),
            'domains'   : card_node.domains_to_json()
        }
    else:
        response = {
            'node' : card_node,
            'homologs': homologs
        }
    if request.is_ajax():
        return render(request, 'NetExplorer/gene_card.html', response)
    else:
        return render(request, 'NetExplorer/gene_card_fullscreen.html', response)


# ------------------------------------------------------------------------------
def gene_search(request):
    '''
    This is the text-based database search function.
    '''
    if request.method == "GET" and "genesymbol" in request.GET:

        # Get Form input
        symbols      = request.GET['genesymbol']
        database     = None
        if "database" in request.GET and request.GET['database']:
            database = request.GET['database']
        nodes        = list()
        search_error = False

        if symbol_is_empty(symbols) is False: # If there is a search term
            symbols = symbols.split(",")
            if database is None: # No database selected
                search_error = 2
                return render(request, 'NetExplorer/gene_search.html', {'res': nodes, 'search_error': search_error, 'databases': sorted(DATABASES) } )

            if database == "Human":
                symbols = substitue_wildcards(symbols)
            else:
                symbols = substitute_human_symbols(symbols, database)
            if not symbols:
                search_error = 1
                return render(request,'NetExplorer/gene_search.html', {'search_error': search_error, 'databases': sorted(DATABASES) } )
            for genesymbol in symbols:
                try:
                    search_node = query_node(genesymbol, database)
                    nodes.append(search_node)
                except (NodeNotFound, IncorrectDatabase):
                    logging.info("ERROR: NodeNotFound or IncorrectDatabase in gene_search")
                    # No search results...
                    search_error = 1

            return render(request, 'NetExplorer/gene_search.html', {'res': nodes, 'search_error': search_error, 'databases': sorted(DATABASES) } )

        # Render when user enters the page
        return render(request, 'NetExplorer/gene_search.html', {'databases': sorted(DATABASES) })
    else:
        return render(request, 'NetExplorer/gene_search.html', {'databases': sorted(DATABASES) })


# ------------------------------------------------------------------------------
def net_explorer(request):
    '''
    This is the cytoscape graph-based search function.
    '''
    if request.method == "GET" and "genesymbol" in request.GET and request.is_ajax():
        symbols  = request.GET['genesymbol']
        if symbol_is_empty(symbols):
            return HttpResponse(status=400)
        symbols  = symbols.split(",")
        database = None

        if "database" in request.GET:
            database     = request.GET['database']
        else:
            logging.info("ERROR: No database in net_explorer")
            return HttpResponse(status=400)

        if request.GET['type'] == "node":
            # ADDING NODES USING CONTIG_IDS, PROTEIN SYMBOLS, GO CODES OR PFAM IDENTIFIERS
            symbols   = substitute_human_symbols(symbols, database)
            graphobject = GraphCytoscape()
            if database is not None:
                for symbol in symbols:
                    try:
                        search_node  = query_node(symbol, database)
                        nodes, edges = search_node.get_graphelements()
                        graphobject.add_elements(nodes)
                        graphobject.add_elements(edges)
                    except (NodeNotFound, IncorrectDatabase) as err:
                        logging.info("ERROR: NodeNotFound or IncorrectDatabase in net_e")
                        continue
            if graphobject.is_empty():
                return HttpResponse(status=404)
            else:
                graphobject.define_important(set(symbols))
                json_data = graphobject.to_json()
                return HttpResponse(json_data, content_type="application/json")
        else:
            # ADDING A PATHWAY USING KEGG CODES
            kegg_url = "http://togows.dbcls.jp/entry/pathway/%s/genes.json" % symbols[0]
            # Try to connect to the web and extract its contents
            r = requests.get(kegg_url)
            if r.status_code == 200: # Success
                if r.json():
                    gene_list = [gene.split(";")[0] for gene in r.json()[0].values()]
                    gene_list = substitute_human_symbols(gene_list, database)
                    databases = [database] * len(gene_list)
                    graphelements = get_subgraph(gene_list, databases)
                    if graphelements:
                        return HttpResponse(graphelements, content_type="application/json")
                    else:
                        return HttpResponse(status=404)
                else: # Empty json
                    return HttpResponse(status=404)
            else: # Something went wrong
                return HttpResponse(status=404)
    elif request.method == "POST":
        json_text = None
        if 'json_text' in request.POST:
            json_text = request.POST['json_text']
        render_to_return = upload_graph(request, json_text)
        return render_to_return
    else:
        # Get experiment data to put it on the Map Expression dialog Form
        all_experiments = ExperimentList()
        return render(request, 'NetExplorer/netexplorer.html', { 'experiments': all_experiments, 'databases': sorted(DATABASES)} )


# ------------------------------------------------------------------------------
def show_connections(request):
    """
    View that handles an AJAX request and, given a list of identifiers, returns
    all the interactions between those identifiers/nodes.
    """
    if request.is_ajax():
        nodes_including = request.GET['nodes'].split(",")
        databases       = request.GET['databases'].split(",")
        graphelements   = get_subgraph(nodes_including, databases)
        return HttpResponse(graphelements, content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')

# ------------------------------------------------------------------------------
def upload_graph(request, json_text):
    """
    This function will take the request with a JSON file and it will return
    a template with the graph loaded (it will also handle the errors).
    It will return a render object to be returned by net_explorer view.
    """
    # JSON with graph uploaded
    graph_content = str()
    no_layout     = 0
    if json_text is None:
        graph_content   = request.FILES['myfile'].read()
        graph_content   = graph_content.replace("\xef\xbb\xbf", "") # Remove unicode BOM
        graph_content.replace("'", '"') # Json only allows double quotes
    else:
        graph_content = json_text
        no_layout = 1

    try: # Check if file is a valid JSON
        json_graph = json.loads(graph_content)
        all_experiments = ExperimentList()
        try: # Check if JSON is a graph declaration
            json_graph[u'nodes']
        except KeyError:
            logging.info("ERROR: Json is not a graph declaration (no nodes) in upload_graph")
            return render(request, 'NetExplorer/netexplorer.html', {'json_err': True,'databases': sorted(DATABASES), 'experiments': all_experiments})
    except ValueError as err:
        logging.info("ERROR: Not a valid Json File %s in upload_graph\n" % (err))
        return render(request, 'NetExplorer/netexplorer.html', {'json_err': True,'databases': sorted(DATABASES)})
    return render(request, 'NetExplorer/netexplorer.html', {'upload_json': graph_content, 'no_layout': no_layout,'databases': sorted(DATABASES), 'experiments': all_experiments})


# ------------------------------------------------------------------------------
def blast(request):
    """
    View for the BLAST form page
    """
    if request.POST:
        if not request.POST['database']:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "No Database selected", 'databases': sorted(DATABASES)})
        if "type" not in  request.POST or not request.POST['type']:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "No valid BLAST application selected",'databases': sorted(DATABASES)})

        fasta = str()
        database = request.POST['database'].lower()
        results = list()
        if request.FILES:
            logging.info("There is a file")
            # Must check if FASTA
            fasta = request.FILES['fastafile'].read()
        else:
            logging.info("No-file")
            # Must check if FASTA/plain or otherwise not valid
            fasta = request.POST['fasta_plain']

        if not fasta:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "No query", 'databases': sorted(DATABASES)})

        # Check length of sequence/number of sequences
        joined_sequences = list()
        numseq           = 0
        for line in fasta.split("\n"):
            if not line:
                continue
            if line[0] == ">":
                numseq += 1
                continue
            joined_sequences.append(line.strip())
        joined_sequences = "".join(joined_sequences)

        if numseq > MAX_NUMSEQ:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "Too many query sequences (> 50)", 'databases': sorted(DATABASES)})
        elif len(joined_sequences) >  MAX_CHAR_LENGTH:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "Query sequence too long (> 25,000 characters)", 'databases': sorted(DATABASES)})

        # Create temp file with the sequences
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(fasta)
            temp.flush()

            # Run BLAST
            pipe = Popen([request.POST['type'], "-evalue", "1e-10", "-db", BLAST_DB_DIR + database , "-query", temp.name, '-outfmt', '6'], stdout=PIPE, stderr=STDOUT)
            stdout, stderr = pipe.communicate()
            results = [ line.split("\t") for line in stdout.split("\n") if line ]
        if results:
            return render(request, 'NetExplorer/blast.html', {'results': results, 'database': database.title(), 'databases': sorted(DATABASES) })
        else:
            return render(request, 'NetExplorer/blast.html', {'results': results, 'noresults': True, 'database': database.title(), 'databases': sorted(DATABASES) })
    else:
        return render(request, 'NetExplorer/blast.html',{'databases': sorted(DATABASES)})

# ------------------------------------------------------------------------------
def map_expression(request):
    """
    View to handle a possible ajax request to map expression onto graph
    """
    if request.is_ajax():
        nodes      = request.GET['nodes'].split(",")
        databases  = request.GET['databases'].split(",")
        sample     = request.GET['sample']
        to_color   = request.GET['to_color']
        from_color = request.GET['from_color']
        comp_type  = request.GET['type'] # Can be 'one-sample' or 'two-sample'
        # Check if experiment is in DB
        response = dict()
        response['status']     = ""
        response['experiment'] = ""
        response['expression']       = ""
        try:
            experiment = Experiment(request.GET['experiment'])
            experiment.color_gradient(from_color, to_color, comp_type)
            response['experiment'] = experiment.to_json()
        except ExperimentNotFound as err:
            logging.info(err)
            response['status'] = "no-expression"
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json; charset=utf8')
        if comp_type == "two-sample":
            # We have to samples to compare
            sample = sample.split(":")
        else:
            sample = [sample]

        newgraph = GraphCytoscape()
        newgraph.add_elements([ PredictedNode(node, database, query=False) for node, database in zip(nodes, databases) ])
        expression_data = newgraph.get_expression(experiment, sample)
        response['expression'] = dict()
        if comp_type == "two-sample":
            foldchange = dict()
            for node in expression_data:
                exp_sample1 = expression_data[node][sample[0]]
                exp_sample2 = expression_data[node][sample[1]]
                if exp_sample1 == 0 or exp_sample2 == 0:
                    # Don't know how to deal with zeros
                    continue
                foldchange[node] = dict()
                foldchange[node]["foldchange"] = math.log10(exp_sample2 / exp_sample1) / math.log10(2)
            # Now remove samples from list sample and add new key to expression_data dictionary with
            # fold changes.
            sample = list()
            sample.append("foldchange")
            expression_data = foldchange

        for node in expression_data:
            for bin_exp in experiment.gradient:
                if expression_data[node][sample[0]] >= bin_exp[0]:
                    response['expression'][node] = bin_exp[1] # Color
                else:
                    continue
        if not response['expression']:
            response['status'] = "no-expression"
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json; charset=utf8')
        else:
            response['expression']  = json.dumps(response['expression'])
            response['type']        = comp_type
            response = json.dumps(response)
            return HttpResponse(response, content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')

# ------------------------------------------------------------------------------
def path_finder(request):
    """
    View for the Pathway Finder.
    Returns a list called "graphelements". This is a list of tuples, with the first element
    of the tuple being the JSON of the graph to be used by cytoscape.js, and the second element being
    the score assigned to the given pathway.
    """
    if 'start' in request.GET and 'end' in request.GET:
        # We have a search
        if not request.GET['database']:
            return render(request, 'NetExplorer/pathway_finder.html', {"nodb": True, 'databases': sorted(DATABASES)})
        if symbol_is_empty(request.GET['start']) or symbol_is_empty(request.GET['end']):
            return render(request, 'NetExplorer/pathway_finder.html', {"nonodes": True, 'databases': sorted(DATABASES)})
        if not request.GET['plen']:
            return render(request, 'NetExplorer/pathway_finder.html', {"noplen": True, 'databases': sorted(DATABASES)})
        # Search
        # Valid search
        database   = request.GET['database']
        plen       = request.GET['plen']
        startnodes = list()
        endnodes   = list()
        start_nodes_symbols = substitute_human_symbols([request.GET['start']], database)
        end_nodes_symbols   = substitute_human_symbols([request.GET['end']],   database)

        # Query all the nodes and get node objects
        for symbol in start_nodes_symbols:
            try:
                node = query_node(symbol, database)
                startnodes.append(node)
            except (NodeNotFound, IncorrectDatabase):
                continue

        for symbol in end_nodes_symbols:
            try:
                node = query_node(symbol, database)
                endnodes.append(node)
            except (NodeNotFound, IncorrectDatabase):
                continue

        # Get shortest paths
        graphelements, numpath = get_shortest_paths(
            startnodes,
            endnodes,
            plen
        )
        response = dict()
        response['database']  = database
        response['snode']     = request.GET['start']
        response['enode']     = request.GET['end']
        response["plen"]      = plen
        response["databases"] = sorted(DATABASES)

        if graphelements:
            # We have graphelements to display (there are paths)
            graphelements = sorted(graphelements, key=lambda k: k[1], reverse=True)
            response["pathways"] = graphelements
            response["numpath"]  = numpath
            return render(request, 'NetExplorer/pathway_finder.html', response)
        else:
            # No results
            response['noresults'] = True
            return render(request, 'NetExplorer/pathway_finder.html', response)
    else:
        # Not a search
        response = dict()
        response["databases"] = sorted(DATABASES)
        return render(request, 'NetExplorer/pathway_finder.html', response)


# ------------------------------------------------------------------------------
def tutorial(request):
    """
    View for tutorial
    """
    return render(request, 'NetExplorer/tutorial.html')

# ------------------------------------------------------------------------------
def downloads(request):
    """
    View for downloads
    """
    return render(request, 'NetExplorer/downloads.html')

# ------------------------------------------------------------------------------
def datasets(request):
    """
    View for datasets
    """
    return render(request, 'NetExplorer/datasets.html', {'databases': sorted(DATABASES)})


# ------------------------------------------------------------------------------
def about(request):
    """
    View for about
    """
    return render(request, 'NetExplorer/about.html', {'databases': sorted(DATABASES)})

# ------------------------------------------------------------------------------
def handler404(request):
    """
    Handler for error 404, doesn't work.
    """
    response = render_to_response('NetExplorer/404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


# ------------------------------------------------------------------------------
def handler500(request):
    """
    Handler for error 500 (internal server error), doesn't work.
    """
    response = render_to_response('NetExplorer/500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response
