from .common import *


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
        all_experiments = ExperimentList(request.user)
        try: # Check if JSON is a graph declaration
            json_graph[u'nodes']
        except KeyError:
            logging.info("ERROR: Json is not a graph declaration (no nodes) in upload_graph")
            return render(request, 'NetExplorer/netexplorer.html', {'json_err': True,'databases': Dataset.get_allowed_datasets(request.user), 'experiments': all_experiments})
    except ValueError as err:
        logging.info("ERROR: Not a valid Json File %s in upload_graph\n" % (err))
        return render(request, 'NetExplorer/netexplorer.html', {'json_err': True,'databases': Dataset.get_allowed_datasets(request.user)})
    
    # Check if homologs are defined... 
    # They are not if we are coming from Pathway Finder to save time.
    if u'homolog' not in json_graph[u'nodes'][0][u'data']:
        for node in json_graph[u'nodes']:
            qnode = PlanarianContig(node[u'data'][u'id'], node[u'data'][u'database'])
            if qnode.homolog is not None:
                node[u'data'][u'homolog'] = str(qnode.homolog.human.symbol)
        graph_content = json.dumps(json_graph)
    return render(request, 'NetExplorer/netexplorer.html', {'upload_json': graph_content, 'no_layout': no_layout,'databases': Dataset.get_allowed_datasets(request.user), 'experiments': all_experiments})


def net_explorer(request):
    '''
    This is the cytoscape graph-based search function.
    '''
    if request.method == "GET" and request.is_ajax():
        # CHECK IF FORM IS OK
        if (not "genesymbol" in request.GET or
            not "database" in request.GET or
            symbol_is_empty(request.GET['genesymbol'])):
            return HttpResponse(status=400)
        symbols  = request.GET['genesymbol']
        symbols  = symbols.split(",")
        database = request.GET['database']

        # ADDING NODES USING CONTIG_IDS, PROTEIN SYMBOLS, GO CODES, OR PFAM IDENTIFIERS
        if request.GET['type'] == "node":
            graphobject = GraphCytoscape()
            graphobject.new_nodes(symbols, database)
            # Clone the list of nodes to search for interactions
            nodes_to_search = list(graphobject.nodes)
            for node in nodes_to_search:
                try:
                    node.get_neighbours_shallow()
                    node.important = True
                    nodes, edges = node.get_graphelements()
                    graphobject.add_elements(nodes)
                    graphobject.add_elements(edges)
                except (exceptions.NodeNotFound, exceptions.IncorrectDatabase) as err:
                    continue
            if graphobject.is_empty():
                return HttpResponse(status=404)
            else:
                json_data = graphobject.to_json()
                return HttpResponse(json_data, content_type="application/json")
        # ADDING A PATHWAY USING KEGG CODES
        else:
            kegg = KeggPathway(symbol=symbols[0], database=database)
            if not kegg.is_empty():
                return HttpResponse(kegg.graphelements, content_type="application/json")
            else:
                return HttpResponse(status=404)
    elif request.method == "POST":
        json_text = None
        if 'json_text' in request.POST:
            json_text = request.POST['json_text']
        render_to_return = upload_graph(request, json_text)
        return render_to_return
    else:
        return render(request, 'NetExplorer/netexplorer.html', { 'experiments': ExperimentList(request.user), 'databases': Dataset.get_allowed_datasets(request.user)} )

