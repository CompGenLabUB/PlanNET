from django.shortcuts   import render
from django.shortcuts   import render_to_response
from django.http        import HttpResponse
from django.template    import RequestContext
from NetExplorer.models import PredictedNode, HumanNode, PredInteraction,Document
import textwrap
import json
import re
from pprint import pprint

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
            except:
                # Node is not a human node :_(
                print("Node is not a human node, try next symbol")
                continue

            print("%s does not match %s" %(symbol, symbol_regexp[database]))
    return newsymbols


# ------------------------------------------------------------------------------
def node_to_jsondict(node, query):
    '''
    This function takes a node object and returns a dictionary with the necessary
    structure to convert it to json and be read by cytoscape.js
    '''
    element                     = dict()
    element['data']             = dict()
    element['data']['id']       = node.symbol
    element['data']['name']     = node.symbol
    element['data']['database'] = node.database
    element['data']['homolog']  = node.homolog.human.symbol
    if query:
        element['data']['colorNODE'] = "#449D44"
    else:
        element['data']['colorNODE'] = "#404040"
    return element

# ------------------------------------------------------------------------------
def edge_to_jsondict(edge):
    '''
    This function takes a PredInteraction object and returns a dictionary with the necessary
    structure to convert it to json and be read by cytoscape.js
    '''
    element         = dict()
    element['data'] = dict()
    element['data']['id']          = "-".join(sorted((edge.source_symbol, edge.target.symbol)))
    element['data']['source']      = edge.source_symbol
    element['data']['target']      = edge.target.symbol
    element['data']['pathlength']  = edge.parameters['path_length']
    element['data']['probability'] = edge.parameters['int_prob']

    if edge.parameters['path_length'] == 1:
        element['data']['colorEDGE']   = "#72a555"
    else:
        element['data']['colorEDGE']   = "#CA6347"

    return element

# ------------------------------------------------------------------------------
def get_graph_elements(symbols, database, graphelements, added_elements):
    """
    This function takes the list of symbols from the net_explorer form and
    fills a dictionary with the elements to add to the graph.
    """
    if database is None:
        # No database
        return None
    else:
        for symbol in symbols:
            try:
                search_node = query_node(symbol, database)
                search_node.get_neighbours()

                 # Add search node
                graphelements['nodes'].append( node_to_jsondict(search_node, True) )
                added_elements.add(search_node.symbol)
                print(graphelements)

                for interaction in search_node.neighbours:
                    if interaction.target.symbol not in added_elements and interaction.target.symbol not in symbols:
                        graphelements['nodes'].append( node_to_jsondict(interaction.target, False) )
                        added_elements.add(interaction.target.symbol)
                    added_elements.add((search_node.symbol, interaction.target.symbol))
                    if (interaction.target.symbol, search_node.symbol) not in added_elements:
                        graphelements['edges'].append( edge_to_jsondict(interaction) )
            except:
                print("node not found")
    return

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
    except:
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

    try:
        card_node = query_node(symbol, database)
        card_node.get_neighbours()
        card_node.get_domains()
    except Exception as e:
        return render(request, 'NetExplorer/404.html')

    if request.is_ajax():
        return render(request, 'NetExplorer/gene_card.html', { 'node': card_node })
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
        if "database" in request.GET:
            database = request.GET['database']
        nodes        = list()
        search_error = False

        if symbols: # If there is a search term
            symbols = symbols.split(",")
            if database is None: # No database selected
                search_error = 2
                return render(request, 'NetExplorer/gene_searcher.html', {'res': nodes, 'search_error': search_error } )

            for genesymbol in symbols:
                try:
                    search_node = query_node(genesymbol, database)
                    nodes.append(search_node)
                except Exception as e:
                    # No search results...
                    search_error = 1

            return render(request, 'NetExplorer/gene_searcher.html', {'res': nodes, 'search_error': search_error } )

        # Render when user enters the page
        return render(request, 'NetExplorer/gene_searcher.html' )
    else:
        return render(request, 'NetExplorer/gene_searcher.html')


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

        graphelements    = {'nodes': list(), 'edges': list()}
        added_elements   = set()

        symbols = substitute_human_symbols(symbols, database)

        get_graph_elements(symbols, database, graphelements, added_elements)
        json_data = json.dumps(graphelements)

        # Expand graph on click
        if not graphelements['edges'] and not graphelements['nodes']:
            # No nodes nor edges!
            json_data = ""

        print(json_data)
        return HttpResponse(json_data, content_type="application/json")

    elif request.method == "POST":
        json_text = None
        if 'json_text' in request.POST:
            json_text = request.POST['json_text']
        render_to_return = upload_graph(request, json_text)
        return render_to_return
    else:
        return render(request, 'NetExplorer/cytoscape_explorer.html')

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
            return render(request, 'NetExplorer/cytoscape_explorer.html', {'json_err': True})
    except ValueError as err:
        print("Not a valid Json File %s\n" % (err))
        return render(request, 'NetExplorer/cytoscape_explorer.html', {'json_err': True})

    return render(request, 'NetExplorer/cytoscape_explorer.html', {'upload_json': graph_content, 'no_layout': no_layout})


# ------------------------------------------------------------------------------
def blast(request):
    """
    View for the BLAST form page
    """
    return render(request, 'NetExplorer/404.html')


# ------------------------------------------------------------------------------
def path_finder(request):
    """
    View for the Pathway Finder.
    Returns a list called "graphelements". This is a list of tuples, with the first element
    of the tuple being the JSON of the graph to be used by cytoscape.js, and the second element being
    the score assigned to the given pathway.
    """
    if request.method == "GET":
        if 'start' in request.GET and 'end' in request.GET:
            # Search
            if request.GET['start'] and request.GET['end'] and request.GET['database']:
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
                    except:
                        continue

                for symbol in end_nodes_symbols:
                    try:
                        node = query_node(symbol, database)
                        endnodes.append(node)
                    except:
                        continue

                # Get shortest paths
                graphelements = list()
                numpath = 0
                plen    = 0
                for snode in startnodes:
                    for enode in endnodes:
                        paths = snode.path_to_node(enode, including, excluding)
                        plen = len(paths[0]['edges'])
                        if paths is None:
                            # Return no-path that matches the query_node
                            continue
                        else:
                            for p in paths:
                                graphelements.append({'nodes': list(), 'edges': list()})
                                for edge in p['edges']:
                                    graphelements[numpath]['edges'].append(edge_to_jsondict(edge))
                                for node in p['nodes']:
                                    graphelements[numpath]['nodes'].append(node_to_jsondict(node, False))
                                graphelements[numpath] = (json.dumps(graphelements[numpath]), round(p['score'], 2))
                                numpath += 1
                if graphelements:
                    # We have graphelements to display (there are paths)

                    graphelements = sorted(graphelements, key=lambda k: k[1], reverse=True)
                    response = {
                        "pathways" : graphelements,
                        "plen"     : plen,
                        "numpath"  : numpath,
                        "database" : database,
                        "snode"    : request.GET['start'],
                        "enode"    : request.GET['end']
                    }
                    return render(request, 'NetExplorer/pathway_finder.html', response)
                else:
                    return render(request, 'NetExplorer/pathway_finder.html')
            else:
                # Not valid search
                return render(request, 'NetExplorer/pathway_finder.html')
        else:
            # Not a search
            return render(request, 'NetExplorer/pathway_finder.html')


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
    response = render_to_response('NetExplorer/500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response
