from .common import *

def downloader(request):
    """
    Handles the download of sequence and annotations
    """
    MAX_IDS = 10000
    databases = Dataset.get_allowed_datasets(request.user)
    if 'identifiers' not in request.POST:
        return render(request, 'NetExplorer/downloads.html', { 'databases': databases })
    if 'database' not in request.POST or not request.POST['database']:
        return render(request, 'NetExplorer/downloads.html', { 'databases': databases, 'error': 'database' })
    if 'data' not in request.POST or not request.POST['data']:
        return render(request, 'NetExplorer/downloads.html', { 'databases': databases, 'error': 'data' })

    identifiers = request.POST['identifiers']
    identifiers = re.split(r"[\n\r,;]+", identifiers)
    identifiers = [ symbol.replace(" ", "") for symbol in identifiers ]
    if len(identifiers) > MAX_IDS and not request.user.is_authenticated():
        identifiers = identifiers[0:MAX_IDS]
    database = request.POST['database']
    data = request.POST['data']
    dhandler = downloaders.DownloadHandler()
    the_file = dhandler.download_data(identifiers, database, data)
    response = the_file.to_response()
    return response