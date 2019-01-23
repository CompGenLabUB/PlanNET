from .common import *

def datasets(request):
    """
    View for datasets
    """
    datasets = Dataset.get_allowed_datasets(request.user)
    return render(request, 'NetExplorer/datasets.html', {'databases': datasets})