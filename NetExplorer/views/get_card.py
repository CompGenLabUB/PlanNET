from .common import *

def get_card(request, symbol=None, database=None):
    """
    Function that gets a gene id and a database and returns the HTML of the card.
    """
    if request.method == 'GET' and request.is_ajax():
        symbol    = request.GET['target']
        database  = request.GET['targetDB']
        template  = ""
    try:
        gsearch = GeneSearch(symbol, database)
        if database == "Human":
            template = "NetExplorer/human_card.html"
            card_node = gsearch.get_human_genes()[0]
            homologs = card_node.get_homologs()
            card_node.get_summary()
            all_databases = Dataset.get_allowed_datasets(request.user)
            sorted_homologs = list()
            for db in all_databases:
                if db.name in homologs:
                    sorted_homologs.append((db.name, homologs[db.name]))
                else:
                    sorted_homologs.append((db.name, list()))
        elif database == "Smesgene":
            template = "NetExplorer/smesgene_card.html"
            card_node = gsearch.get_planarian_genes()[0]
            contigs = card_node.get_planarian_contigs()
            best_contig = card_node.get_best_transcript()
            best_contig.get_homolog()
            best_contig.get_neighbours()
            best_contig.get_geneontology()
            if best_contig.homolog:
                best_contig.homolog.human.get_summary()
            nodes, edges = best_contig.get_graphelements()
            graph = GraphCytoscape()
            graph.add_elements(nodes)
            graph.add_elements(edges)
        else:
            template = "NetExplorer/contig_card.html"
            card_node = gsearch.get_planarian_contigs()[0]
            card_node.get_summary()
            card_node.get_neighbours()
            card_node.get_domains()
            card_node.get_geneontology()
            nodes, edges = card_node.get_graphelements()
            graph = GraphCytoscape()
            graph.add_elements(nodes)
            graph.add_elements(edges)
    except Exception as err:
        return render_to_response('NetExplorer/not_interactome.html')
    if database == "Human":
       response = {
            'node' : card_node,
            'homologs': sorted_homologs
        }
    elif database == "Smesgene":
        response = {
            'node': card_node,
            'transcripts': contigs,
            'best_transcript': best_contig,
            'json_graph': graph.to_json()
        }
    else:
        response = {
            'node'      : card_node,
            'json_graph': graph.to_json(),
            'domains'   : card_node.domains_to_json()
        }
    
    if request.is_ajax():
        return render(request, template, response)
    else:
        return render(request, 'NetExplorer/gene_card_fullscreen.html', response)