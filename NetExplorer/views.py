"""
Views of PlanNet
"""

from django.shortcuts   import render
from django.shortcuts   import render_to_response
from django.http        import HttpResponse
from django.template    import RequestContext
from NetExplorer.models import PredictedNode, HumanNode, Document, NodeNotFound, IncorrectDatabase, GraphCytoscape
from subprocess import Popen, PIPE, STDOUT
from django.contrib.staticfiles.templatetags.staticfiles import static
import tempfile
import textwrap
import json
import re
import sys

# -----------------------
# CONSTANTS
# -----------------------
BLAST_DB_DIR = "/home/sergio/code/PlaNET/blast/"

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
    if database == "Human":
        node = HumanNode(symbol, database)
    else:
        node = PredictedNode(symbol, database)
        node.get_summary()

    return node


# ------------------------------------------------------------------------------
def get_shortest_paths(startnodes, endnodes, including, excluding):
    '''
    This function gets all the possible shortest paths between the specified nodes.
    Returns a json string with all the nodes and edges, the length of the paths and
    the total number of paths
    '''
    graphelements = list()
    numpath = 0
    plen    = 0
    for snode in startnodes:
        for enode in endnodes:
            paths = snode.path_to_node(enode, including, excluding)
            plen = len(paths[0]['graph'].edges)
            if paths is None:
                # Return no-path that matches the query_node
                continue
            else:
                for path in paths:
                    graphelements.append( GraphCytoscape() )
                    graphelements[numpath].add_elements(path['graph'].nodes)
                    graphelements[numpath].add_elements(path['graph'].edges)
                    graphelements[numpath] = (graphelements[numpath].to_json, round(path['score'], 2))
                    numpath += 1
    return graphelements, plen, numpath


# ------------------------------------------------------------------------------
def substitute_human_symbols(symbols, database):
    """
    This function will get a list of symbols and it will substitute all human symbols by
    the "homologs" of the specified database. It will return the "new" list of symbols
    """
    symbol_regexp = {
        "Cthulhu":      "cth1_",
        "Consolidated": "OX_Smed"
    }

    newsymbols = list()
    for symbol in symbols:
        symbol = symbol.replace(" ", "")
        if re.match(symbol_regexp[database], symbol):
            newsymbols.append(symbol)
        else:
            # Human node!
            try:
                symbol = symbol.upper()
                human_node = HumanNode(symbol, "Human")
                homologs   = human_node.get_homologs(database)
                for hom in homologs:
                    newsymbols.append(hom.prednode.symbol)
            except (NodeNotFound, IncorrectDatabase):
                # Node is not a human node :_(
                print("Node is not a human node, try next symbol")
                continue

            print("%s does not match %s" %(symbol, symbol_regexp[database]))
    return newsymbols


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

    card_node = None
    json_data = None
    try:
        card_node = query_node(symbol, database)
        card_node.get_domains()
        nodes, edges =card_node.get_graphelements()
        graph = GraphCytoscape()
        graph.add_elements(nodes)
        graph.add_elements(edges)
        json_data = graph.to_json()
    except (NodeNotFound, IncorrectDatabase):
        return render(request, 'NetExplorer/404.html')

    if request.is_ajax():
        return render(request, 'NetExplorer/gene_card.html', { 'node': card_node, 'json_data': json_data })
    else:
        return render(request, 'NetExplorer/gene_card_fullscreen.html', { 'node': card_node })


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

        if symbols: # If there is a search term
            symbols = symbols.split(",")
            if database is None: # No database selected
                search_error = 2
                return render(request, 'NetExplorer/gene_search.html', {'res': nodes, 'search_error': search_error } )

            for genesymbol in symbols:
                try:
                    search_node = query_node(genesymbol, database)
                    nodes.append(search_node)
                except (NodeNotFound, IncorrectDatabase):
                    # No search results...
                    search_error = 1

            return render(request, 'NetExplorer/gene_search.html', {'res': nodes, 'search_error': search_error } )

        # Render when user enters the page
        return render(request, 'NetExplorer/gene_search.html' )
    else:
        return render(request, 'NetExplorer/gene_search.html')


# ------------------------------------------------------------------------------
def net_explorer(request):
    '''
    This is the cytoscape graph-based search function.
    '''
    if request.method == "GET" and "genesymbol" in request.GET and request.is_ajax():
        symbols  = request.GET['genesymbol']
        symbols  = symbols.split(",")
        database = None

        if "database" in request.GET:
            database     = request.GET['database']
        else:
            print("NO DATABASE")

        symbols       = substitute_human_symbols(symbols, database)
        graphobject   = GraphCytoscape()
        if database is not None:
            for symbol in symbols:
                try:
                    search_node  = query_node(symbol, database)
                    nodes, edges = search_node.get_graphelements()
                    graphobject.add_elements(nodes)
                    graphobject.add_elements(edges)
                except (NodeNotFound, IncorrectDatabase):
                    continue
        if graphobject.is_empty():
            return HttpResponse(status_code=400)
        else:
            graphobject.define_important(set(symbols))
            json_data = graphobject.to_json()
            return HttpResponse(json_data, content_type="application/json")
    elif request.method == "POST":
        json_text = None
        if 'json_text' in request.POST:
            json_text = request.POST['json_text']
        render_to_return = upload_graph(request, json_text)
        return render_to_return
    else:
        return render(request, 'NetExplorer/netexplorer.html')


# ------------------------------------------------------------------------------
def show_connections(request):
    """
    View that handles an AJAX request and, given a list of identifiers, returns
    all the interactions between those identifiers/nodes.
    """
    if request.is_ajax():
        nodes_including = request.GET['nodes'].split(",")
        databases       = request.GET['databases'].split(",")
        graph           = GraphCytoscape()
        for node_id, database in zip(nodes_including, databases):
            node = query_node(node_id, database)
            nodes, edges = node.get_graphelements()
            graph.add_elements(nodes)
            graph.add_elements(edges)
        graph.filter( set(nodes_including) )
        graphelements = graph.to_json()
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
        try: # Check if JSON is a graph declaration
            json_graph[u'nodes']
        except KeyError:
            print("Json is not a graph declaration (no nodes)")
            return render(request, 'NetExplorer/netexplorer.html', {'json_err': True})
    except ValueError as err:
        print("Not a valid Json File %s\n" % (err))
        return render(request, 'NetExplorer/netexplorer.html', {'json_err': True})

    return render(request, 'NetExplorer/netexplorer.html', {'upload_json': graph_content, 'no_layout': no_layout})


# ------------------------------------------------------------------------------
def blast(request):
    """
    View for the BLAST form page
    """
    if request.POST:
        if not request.POST['database']:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "No Database selected"})
        if "type" not in  request.POST or not request.POST['type']:
            return render(request, 'NetExplorer/blast.html', {"error_msg": "No valid BLAST application selected"})

        fasta = str()
        database = request.POST['database'].lower()
        results = list()
        if request.FILES:
            print("There is a file")
            # Must check if FASTA
            fasta = request.FILES['fastafile'].read()

        else:
            print("No-file")
            # Must check if FASTA/plain or otherwise not valid
            fasta = request.POST['fasta_plain']

        # Create temp file with the sequences
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(fasta)
            temp.flush()

            # Run BLAST
            pipe = Popen([request.POST['type'], "-db", BLAST_DB_DIR + database , "-query", temp.name, '-outfmt', '6'], stdout=PIPE, stderr=STDOUT)
            stdout, stderr = pipe.communicate()
            results = [ line.split("\t") for line in stdout.split("\n") if line ]
        return render(request, 'NetExplorer/blast.html', {'results': results })
    else:
        return render(request, 'NetExplorer/blast.html')

# query id, subject id, % identity, alignment length, mismatches, gap opens, q. start, q. end, s. start, s. end, evalue, bit score

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
            return render(request, 'NetExplorer/pathway_finder.html', {"nodb": True})
        if not request.GET['start'] or not request.GET['end']:
            return render(request, 'NetExplorer/pathway_finder.html', {"nonodes": True})

        # Search
        # Valid search
        database = request.GET['database']
        startnodes = list()
        endnodes   = list()
        including  = None
        excluding  = None

        if request.GET['including']:
            including = request.GET['including'].split(",")
        if request.GET['excluding']:
            excluding = request.GET['excluding'].split(",")

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
        graphelements, plen, numpath = get_shortest_paths(
            startnodes,
            endnodes,
            including,
            excluding
        )
        response = dict()
        response['database'] = database
        response['snode']    = request.GET['start']
        response['enode']    = request.GET['end']

        if graphelements:
            # We have graphelements to display (there are paths)
            graphelements = sorted(graphelements, key=lambda k: k[1], reverse=True)
            response["pathways"] = graphelements
            response["numpath"]  = numpath
            response["plen"]     = plen
            return render(request, 'NetExplorer/pathway_finder.html', response)
        else:
            # No results
            response['noresults'] = True
            return render(request, 'NetExplorer/pathway_finder.html', response)
    else:
        # Not a search
        return render(request, 'NetExplorer/pathway_finder.html')


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
def about(request):
    """
    View for about
    """
    return render(request, 'NetExplorer/about.html')

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
