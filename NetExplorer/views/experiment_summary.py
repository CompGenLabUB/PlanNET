from .common import *

def experiment_summary(request):
    """
    View from PlanExp that returns information about a given experiment
    """
    if request.is_ajax():
        exp_name = request.GET['experiment']
        # Get Experiment and Conditions
        experiment = Experiment.objects.get(name=exp_name)
        conditions = Condition.objects.filter(experiment__name=exp_name)
        condition_list = dict()
        for condition in conditions:
            if condition.cond_type.name not in condition_list:
                condition_list[condition.cond_type.name] = list()
            condition_list[condition.cond_type.name].append(condition)

        response = dict()
        response_to_render = { 'experiment': experiment, 'conditions': condition_list }
        response['html'] = render_to_string('NetExplorer/experiment_summary.html', response_to_render)
        response['exp_type'] = experiment.exp_type.exp_type
        return HttpResponse(json.dumps(response), content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')