from django.shortcuts   import render
from django.shortcuts   import render_to_response
from django.http        import HttpResponse, HttpResponseRedirect, Http404
from django.template    import RequestContext
from py2neo             import Graph, Path
from NetExplorer.models import PredictedNode, HumanNode, graph, PredInteraction
import tempfile
import textwrap


# -----------------------
# FUNCTIONS
# -----------------------

def query_node(symbol, database):
    '''
    This simple function takes a symbol and a database and tries to get it from
    the DB
    '''
    node = None
    if database == "Human":
        node = HumanNode(symbol, database)
    else:
        node = PredictedNode(symbol, database)
        node.get_summary()

    return node

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
    if request.method == 'GET' and request.is_ajax():
        symbol    = request.GET['target']
        database  = request.GET['targetDB']

    card_node = None

    try:
        card_node = query_node(symbol, database)
        card_node.get_neighbours()
        card_node.get_homolog()
        card_node.get_domains()
    except Exception as e:
        return render(request, 'NetExplorer/404.html')

    if request.is_ajax():
        return render(request, 'NetExplorer/gene_card.html', { 'node': card_node })
    else:
        return render(request, 'NetExplorer/gene_card_fullscreen.html', { 'node': card_node })


# ------------------------------------------------------------------------------
def gene_searcher(request):
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
    if request.method == "GET" and "genesymbol" in request.GET:
        return render(request, 'NetExplorer/cytoscape_explorer.html', {'hola': "hello"})
    else:
        return render(request, 'NetExplorer/net_explorer.html', {'hola': "hello"})


# ------------------------------------------------------------------------------
def handler404(request):
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
