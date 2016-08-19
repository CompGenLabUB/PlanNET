from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

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
        genesymbol = request.GET['genesymbol']
        database   = request.GET['database']
        msg = "You searched for "
        if genesymbol:
            msg = msg + genesymbol + " in %s" % database
        else:
            msg = msg + "nothing"
        return render(request, 'NetExplorer/gene_searcher.html', {'msg': msg} )
    else:
        return render(request, 'NetExplorer/gene_searcher.html', {'msg': "HELLO WORLD"} )

def net_explorer(request):
    '''
    This is the cytoscape graph-based search function.
    '''
