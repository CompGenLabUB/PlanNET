from .common import *

def show_connections(request):
    """
    View that handles an AJAX request and, given a list of identifiers, returns
    all the interactions between those identifiers/nodes.
    """
    if request.is_ajax():
        nodes_including = request.POST['nodes'].split(",")
        databases       = request.POST['databases'].split(",")
        graphelements   = GraphCytoscape()
        for symbol, database in zip(nodes_including, databases):
            graphelements.add_node( PlanarianContig(symbol, database, query=False) )
        graphelements.get_connections()
        return HttpResponse(graphelements, content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')