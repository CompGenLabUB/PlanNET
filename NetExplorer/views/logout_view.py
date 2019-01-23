from .common import *

def logout_view(request):
    """
    Logout view
    """
    logout(request)
    return render(request, 'NetExplorer/index.html')