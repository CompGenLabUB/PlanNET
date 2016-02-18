from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

# -----------------------
# VIEWS
# -----------------------

def index_view(request):
    '''
    This is the first view the user sees.
    It contains the forms, a mini-tutorial, etc.
    '''
    return render(request, 'NetExplorer/index.html', {'msg': "HELLO WORLD"} )
