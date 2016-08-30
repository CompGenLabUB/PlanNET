from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from py2neo import Graph, Path
from NetExplorer.models import PredictedNode, HumanNode, graph
import tempfile
import textwrap
from django.http import HttpResponse

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
    if request.method == "GET" and "genesymbol" in request.GET:
        graph = Graph("http://localhost:7474/db/data/")

    genesymbol   = request.GET['genesymbol']
    typeseq      = request.GET['type']
    if "database" in request.GET:
        database = request.GET['database']
    else:
        pass # server error!!

    node = None
    try:
        if database == "Human":
            node = HumanNode(genesymbol, database)
        else:
            node = PredictedNode(genesymbol, database)
    except:
        pass # server error!

    sequence = str()
    if typeseq == "sequence":
        sequence = textwrap.fill(node.sequence, 70)
    elif typeseq == "orf":
        sequence = textwrap.fill(node.orf, 70)

    sequence = ">%s\n" % node.symbol + sequence
    response = HttpResponse(sequence, content_type='text/plain; charset=utf8')
    filename = "%s.fa" % node.symbol
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


# ------------------------------------------------------------------------------
def get_card(request):
    if request.method == 'GET':
        symbol    = request.GET['target']
        database  = request.GET['targetDB']
        current   = None
        print("DENTRO")
        if "current" in request.GET:
            # We are already in a gene-card save it and send to template to create
            # a back button
            current    = request.GET['current']
            current_db = request.GET['currentDB']
            if current == symbol:
                current    = None
                current_db = None

        card_node = None
        print("%s and %s" %(symbol, database))
        graph = Graph("http://localhost:7474/db/data/")

        try:
            if database == "Human":
                card_node = HumanNode(symbol, database)
            else:
                card_node = PredictedNode(symbol, database)
        except Exception as e:
            pass # 404 -> Card node ID not found... :(

        if current is None:
            return render(request, 'NetExplorer/gene_card.html', { 'node': card_node} )
        else:
            print("P: %s and %s" % (current, current_db))
            return render(request, 'NetExplorer/gene_card.html', { 'node': card_node, 'previous': current, 'previousDB': current_db } )
    else:
        # Error 404
        pass


# ------------------------------------------------------------------------------
def gene_searcher(request):
    '''
    This is the text-based database search function.
    '''
    if request.method == "GET" and "genesymbol" in request.GET:
        graph = Graph("http://localhost:7474/db/data/")

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
                    if database == "Human":
                        search_node = HumanNode(genesymbol, database)
                    else:
                        search_node = PredictedNode(genesymbol, database)
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
    return render(request, 'NetExplorer/net_explorer.html', {'hola': "hello"})
