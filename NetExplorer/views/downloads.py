from .common import *

def downloads(request):
    """
    View for downloads
    """
    response = dict()
    response['databases'] = Dataset.get_allowed_datasets(request.user)
    return render(request, 'NetExplorer/downloads.html', response)
