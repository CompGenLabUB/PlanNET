from .common import *

def map_expression(request):
    """
    View to handle a possible ajax request to map expression onto graph
    """
    if request.is_ajax():
        nodes      = request.GET['nodes'].split(",")
        databases  = request.GET['databases'].split(",")
        sample     = request.GET['sample']
        to_color   = request.GET['to_color']
        from_color = request.GET['from_color']
        comp_type  = request.GET['type'] # Can be 'one-sample' or 'two-sample'
        # Check if experiment is in DB
        response = dict()
        response['status']     = ""
        response['experiment'] = ""
        response['expression']       = ""
        try:
            experiment = oldExperiment(request.GET['experiment'])
            experiment.color_gradient(from_color, to_color, comp_type)
            response['experiment'] = experiment.to_json()
        except ExperimentNotFound as err:
            logging.info(err)
            response['status'] = "no-expression"
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json; charset=utf8')
        if comp_type == "two-sample":
            # We have to samples to compare
            sample = sample.split(":")
            response['sample'] = sample
        else:
            sample = [sample]

        newgraph = GraphCytoscape()
        newgraph.add_elements([ PlanarianContig(node, database, query=False) for node, database in zip(nodes, databases) ])
        expression_data = newgraph.get_expression(experiment, sample)
        response['expression'] = dict()
        if comp_type == "two-sample":
            foldchange = dict()
            for node in expression_data:
                exp_sample1 = expression_data[node][sample[0]]
                exp_sample2 = expression_data[node][sample[1]]
                if exp_sample1 == 0 or exp_sample2 == 0:
                    # Don't know how to deal with zeros
                    continue
                foldchange[node] = dict()
                foldchange[node]["foldchange"] = math.log10(exp_sample2 / exp_sample1) / math.log10(2)
            # Now remove samples from list sample and add new key to expression_data dictionary with
            # fold changes.
            sample = list()
            sample.append("foldchange")
            expression_data = foldchange

        for node in expression_data:
            for bin_exp in experiment.gradient:
                if expression_data[node][sample[0]] >= bin_exp[0]:
                    response['expression'][node] = bin_exp[1] # Color
                else:
                    continue
        if not response['expression']:
            response['status'] = "no-expression"
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json; charset=utf8')
        else:
            response['expression']  = json.dumps(response['expression'])
            response['type']        = comp_type
            response = json.dumps(response)
            return HttpResponse(response, content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')