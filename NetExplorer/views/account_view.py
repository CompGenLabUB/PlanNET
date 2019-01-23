from .common import *

def account_view(request):
    """
    View for account options
    """
    if request.user.is_authenticated:
        if request.method == "POST":
            # Check that everything was sent
            if "previous" in request.POST and "pwd1" in request.POST and "pwd2" in request.POST:
                if request.POST['pwd1'] != request.POST['pwd2']:
                    return render(request, 'NetExplorer/account.html', {'error_msg': "New passwords don't match!."})
                if request.POST['pwd1'] == request.POST['previous']:
                    return render(request, 'NetExplorer/account.html', {'error_msg': "New Password must be different to previous password."})
                # Changing a password
                if request.user.check_password(request.POST['previous']):
                    # Everything is correct
                    request.user.set_password(request.POST['pwd1'])
                    request.user.save()
                    return render(request, 'NetExplorer/account.html', {'success_msg': "Password changed successfully."})
                else:
                    return render(request, 'NetExplorer/account.html', {'error_msg': "Incorrect password!."})
            else:
                # Something was not introduced
                return render(request, 'NetExplorer/account.html', {'error_msg': "Please, fill in the camps."})
        return render(request, 'NetExplorer/account.html')
    else:
        return render(request, 'NetExplorer/login.html')