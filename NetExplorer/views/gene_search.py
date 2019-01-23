from .common import *

def gene_search(request):
    '''
    This is the text-based database search function.
    response:
        - symbols
        - database
        - databases
        - search_error
        - res
        - valid_query
    '''
    response = dict()
    response['databases'] = Dataset.get_allowed_datasets(request.user)
    response['valid_query'] = False
    if request.method == "GET" and "genesymbol" in request.GET:
        # Get Form input
        symbols = request.GET['genesymbol']
        database = None
        if "database" in request.GET and request.GET['database']:
            database = request.GET['database']
        nodes = list()
        response['search_error'] = 0
        response['symbols'] = symbols
        response['database'] = database
        if symbol_is_empty(symbols) is False:
            # If there is a search term
            symbols = symbols.split(",")
            if database is None:
                # No database selected
                response['search_error'] = 2
                response['res'] = nodes
            else:
                # Valid search (symbols + database)
                response['valid_query'] = True
                nodes_graph = GraphCytoscape()
                try:
                    nodes_graph.new_nodes(symbols, database)
                except Exception as err:
                    print(err)
                    logging.info("Node not found.")
                if not nodes_graph:
                    response['search_error'] = 1
                else:
                    response['res'] = sorted(list(nodes_graph.nodes), key= lambda x: (x.name, x.symbol) if hasattr(x, 'name') and x.name else ("a", x.symbol)  )
    return render(request, 'NetExplorer/gene_search.html', response)