from .common import *

def do_tsne(experiment, dataset, conditions, gene_symbol, ctype, with_color):
    '''
    Makes tsne plot
    '''
    theplot = ScatterPlot()
    for condition in conditions:
        trace_name = condition.name
        if condition.defines_cell_type is True and condition.cell_type != "Unknown":
            trace_name = condition.cell_type + " (Cluster " + str(condition.name) + ")"
        theplot.add_trace(trace_name)
        samples = Sample.objects.filter(experiment=experiment, samplecondition__condition=condition)
        cell_positions = CellPlotPosition.objects.filter(
            experiment=experiment, dataset=dataset, 
            sample__in=samples
        )

        cell_order = list()
        for cell in cell_positions:
            theplot.add_x(trace_name, float(cell.x_position))
            theplot.add_y(trace_name, float(cell.y_position))
            cell_name = cell.sample.sample_name
            theplot.add_name(trace_name, cell_name)
            cell_order.append(cell.sample.id)

        if with_color is True:
            # Get Gene expression for cells
            cell_expression = ExpressionAbsolute.objects.filter(
                experiment=experiment, dataset=dataset,
                sample__in=samples, gene_symbol=gene_symbol
            )
            if cell_expression:
                # We need a dictionary with {cell_id : cell_expression}
                # so we can keep the same order as cell positions (in cell_order) 
                thedict = dict()
                for cellexp in cell_expression:
                    thedict[cellexp.sample.id] = cellexp.expression_value
                cell_expression = [ thedict[cell_idx] for cell_idx in cell_order ]
                theplot.add_color_to_trace(trace_name, cell_expression)
            else:
                theplot = None
                break
    return theplot


def plot_tsne(request):
    '''
    Plots Tsne plot for Single-Cell experiment
    '''
    if request.is_ajax():
        exp_name = request.GET['experiment']
        dataset = request.GET['dataset']
        gene_names = request.GET['gene_name']
        ctype = request.GET['ctype']
        with_color = json.loads(request.GET.get('withcolor', 'false'))
        gene_names = gene_names.split(",")

        # First disambiguate gene names
        gene_symbol = str()
        for gene_name in gene_names:
            gene_symbol = disambiguate_gene(gene_name, dataset)[0]

        # Get Experiment and conditions
        experiment = Experiment.objects.get(name=exp_name)
        dataset = Dataset.objects.get(name=dataset)
        conditions = Condition.objects.filter(
            experiment=experiment, 
            cond_type=ConditionType.objects.get(name=ctype))

        # Do the plot
        theplot = do_tsne(experiment, dataset, conditions, gene_symbol, ctype, with_color)
        if theplot is not None:
            response = theplot.plot()
        else:
            response = None

        return HttpResponse(json.dumps(response), content_type="application/json")
