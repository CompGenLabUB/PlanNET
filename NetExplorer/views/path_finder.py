from .common import *

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
            return render(request, 'NetExplorer/pathway_finder.html', {"nodb": True, 'databases': get_databases(request)})
        if symbol_is_empty(request.GET['start']) or symbol_is_empty(request.GET['end']):
            return render(request, 'NetExplorer/pathway_finder.html', {"nonodes": True, 'databases': get_databases(request)})
        if not request.GET['plen']:
            return render(request, 'NetExplorer/pathway_finder.html', {"noplen": True, 'databases': get_databases(request)})
        # Search
        # Valid search
        database   = request.GET['database']
        plen       = request.GET['plen']
        start_nodes = GraphCytoscape()
        start_nodes.new_nodes([request.GET['start']], database)
        end_nodes = GraphCytoscape()
        end_nodes.new_nodes([request.GET['end']], database)
        
        # Get shortest paths
        graphelements, numpath = get_shortest_paths(
            start_nodes.nodes,
            end_nodes.nodes,
            plen
        )
        response = dict()
        response['database']  = database
        response['snode']     = request.GET['start']
        response['enode']     = request.GET['end']
        response["plen"]      = plen
        response["databases"] = Dataset.get_allowed_datasets(request.user)

        if graphelements:
            # We have graphelements to display (there are paths)
            graphelements = sorted(graphelements, key=lambda k: k[1], reverse=True)
            #response["pathways"] = graphelements
            response["numpath"]  = numpath
            paginator = Paginator(graphelements, 10) # Show 25 contacts per page
            page = request.GET.get('page')
            try:
                graphs_for_page = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                graphs_for_page = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                graphs_for_page = paginator.page(paginator.num_pages)
            response['pathways'] = graphs_for_page
            return render(request, 'NetExplorer/pathway_finder.html', response)
        else:
            # No results
            response['noresults'] = True
            return render(request, 'NetExplorer/pathway_finder.html', response)
    else:
        # Not a search
        response = dict()
        response["databases"] = Dataset.get_allowed_datasets(request.user)
        return render(request, 'NetExplorer/pathway_finder.html', response)