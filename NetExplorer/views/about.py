from .common import *

def about(request):
    """
    View for about
    """
    return render(request, 'NetExplorer/about.html', {'databases': Dataset.get_allowed_datasets(request.user)})
