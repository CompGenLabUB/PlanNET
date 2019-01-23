from .common import *

def register(request):
    """
    Login view
    """
    if 'usr' in request.POST and 'pwd' in request.POST:
        user = authenticate(username=request.POST['usr'], password=request.POST['pwd'])
        if user is not None:
            # A backend authenticated the credentials
            login(request, user)
            return render(request, 'NetExplorer/index.html')
        else:
            # No backend authenticated the credentials
            return render(request, 'NetExplorer/login.html', {'error_msg': "Incorrect username or password"})
    return render(request, 'NetExplorer/login.html')