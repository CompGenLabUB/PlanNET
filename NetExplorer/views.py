from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from py2neo import Graph, Path
from NetExplorer.models import PredictedNode, HumanNode, graph
import tempfile


def get_text_results(database):
    pass

# -----------------------
# VIEWS
# -----------------------

def index_view(request):
    '''
    This is the first view the user sees.
    It contains the forms, a mini-tutorial, etc.
    And links to all the functions.
    '''

    return render(request, 'NetExplorer/index.html')



def gene_searcher(request):
    '''
    This is the text-based database search function.
    '''
    if request.method == "GET" and "genesymbol" in request.GET:
        graph = Graph("http://localhost:7474/db/data/")

        genesymbol   = request.GET['genesymbol']
        database     = request.GET['database']
        nodes        = list()
        search_error = False

        if genesymbol: # If there is a search term
            try:
                if database == "Human":
                    search_node = HumanNode(genesymbol, database)
                else:
                    search_node = PredictedNode(genesymbol, database)
                nodes.append(search_node)
            except Exception as e:
                search_error = True
                print("NOOOPE" + str(e))

            return render(request, 'NetExplorer/gene_searcher.html', {'res': nodes, 'search_error': search_error } )

        # Render when user enters the page
        return render(request, 'NetExplorer/gene_searcher.html' )
    else:
        return render(request, 'NetExplorer/gene_searcher.html')


def net_explorer(request):
    '''
    This is the cytoscape graph-based search function.
    '''
    return render(request, 'NetExplorer/net_explorer.html', {'hola': "hello"})
