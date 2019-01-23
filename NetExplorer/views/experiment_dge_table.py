from .common import *


def do_volcano_plot(expression):
    '''
    Creates a Volcano plot with a given comparison of conditions.
    '''
    theplot = ScatterPlot()
    trace_name = "Volcano Plot"
    theplot.add_trace(trace_name)
    max_x = 0
    min_x = 0
    max_y = 0
    for gexp in expression:
        x = gexp.fold_change
        y = -(math.log10(gexp.pvalue))
        theplot.add_x(trace_name, x)
        theplot.add_y(trace_name, y)
        theplot.add_name(trace_name, gexp.gene_symbol)

        # Get max and min X
        if min_x == 0:
            min_x = x
        if x > max_x:
            max_x = x
        elif x < min_x:
            min_x = x

        # Get max and min Y
        if y > max_y:
            max_y = y

    bigger_x = max([abs(min_x), abs(max_x)]) + 1
    theplot.set_limits('x', -bigger_x, bigger_x)
    theplot.set_limits('y', 0, max_y + max_y * 0.10) # Add +10% to make plot axis more visible
    theplot.add_units('x', 'log10 ( Fold Change ) ')
    theplot.add_units('y', '-log10 ( pvalue ) ')
    return theplot


def experiment_dge_table(request):
    """
    View from PlanExp that returns the HTML of a table comparing two conditions
    """
    max_genes = 250
    pvalue_threshold = 0.001
    if request.is_ajax():
        exp_name = request.GET['experiment']
        c1_name = request.GET['condition1']
        c2_name = request.GET['condition2']
        dataset_name = request.GET['dataset']
        experiment = Experiment.objects.get(name=exp_name)
        dataset = Dataset.objects.get(name=dataset_name)
        condition1 = Condition.objects.get(name=c1_name, experiment=experiment)
        condition2 = Condition.objects.get(name=c2_name, experiment=experiment)
        expression = ExpressionRelative.objects.filter(
            experiment=experiment, dataset=dataset, 
            condition1=condition1, condition2=condition2, pvalue__lte=pvalue_threshold)
        if not expression:
            # In case condition1 and condition2 are reversed in Database
            expression = ExpressionRelative.objects.filter(
                experiment=experiment, dataset=dataset, 
                condition1=condition2, condition2=condition1, pvalue__lte=pvalue_threshold)

        expression = expression.annotate(abs_fold_change=Func(F('fold_change'), function='ABS')).order_by('-abs_fold_change')[:max_genes]
        response = dict()
        if expression:
            response_to_render = { 'expressions' : expression, 'database': dataset }
            response['table'] = render_to_string('NetExplorer/experiment_dge_table.html', response_to_render)
            response['volcano'] = do_volcano_plot(expression).plot()
            try:
                json.dumps(response)
            except Exception as err:
                print(err)
        return HttpResponse(json.dumps(response), content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')