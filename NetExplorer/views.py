from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from py2neo import Graph, Path

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

        genesymbol = request.GET['genesymbol']
        database   = request.GET['database']

        msg     = "You searched for "
        symbols = list()

        if genesymbol:
            results = graph.run("MATCH (n:%s) WHERE n.symbol = '%s' RETURN n.symbol AS symbol LIMIT 1" % (database, genesymbol))
            for row in results:
                symbols.append(row['symbol'])
            msg = msg + genesymbol + " in %s" % database

            if symbols:
                return render(request, 'NetExplorer/gene_searcher.html', {'msg': msg, 'res': symbols } )
            else:
                return render(request, 'NetExplorer/gene_searcher.html', {'msg': msg, 'res': symbols, 'search_error': 1 } )
        else:
            msg = msg + "nothing"

        # Render when user enters the page
        return render(request, 'NetExplorer/gene_searcher.html', {'msg': msg } )
    else:
        return render(request, 'NetExplorer/gene_searcher.html', {'msg': "HELLO WORLD"} )

def net_explorer(request):
    '''
    This is the cytoscape graph-based search function.
    '''
