from .common import *

def experiment_dataset(request):
    """
    View from PlanExp that returns information about a given experiment
    """
    if request.is_ajax():
        exp_name = request.GET['experiment']
        experiment = Experiment.objects.get(name=exp_name)
        # Get Experiment and Conditions
        datasets = ExperimentDataset.objects.filter(experiment=experiment).values('dataset')
        datasets = Dataset.objects.filter(id__in=datasets)
        serialized_datasets = serializers.serialize('json', datasets)
        return HttpResponse(serialized_datasets, content_type="application/json")
    else:
        return render(request, 'NetExplorer/404.html')