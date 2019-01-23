from .common import *

def tutorial(request):
    """
    View for tutorial
    """
    return render(request, 'NetExplorer/tutorial.html')