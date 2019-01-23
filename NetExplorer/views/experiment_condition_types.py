from .common import *

def experiment_condition_types(request):
    """
    View from PlanExp that returns condition types for a given experiment
    """
    if request.is_ajax():
        exp_name = request.GET['experiment']
        conditions = Condition.objects.filter(experiment__name=exp_name)
        ctypes = ConditionType.objects.filter(condition__in=conditions)
        ctypes = list(set(ctypes.values_list('name', flat=True)))
        return HttpResponse(json.dumps(sorted(ctypes)), content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')