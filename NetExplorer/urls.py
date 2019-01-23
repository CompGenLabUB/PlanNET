from django.conf.urls import url
from . import views
from django.contrib import admin


urlpatterns = [
    url(r'^$', views.index_view, name='index_view'),
    url(r'^gene_search', views.gene_search, name="gene_search"),
    url(r'^net_explorer',  views.net_explorer,  name="net_explorer" ),
    url(r'^planexp',  views.planexp,  name="planexp" ),
    url(r'^gene_card/(?P<database>[0-9\w]+)/(?P<symbol>[0-9\w_\.\/\#\|\%]+)$', views.get_card, name = 'card_fullscreen'),
    url(r'^get_fasta',     views.get_fasta,       name="get_fasta"),
    url(r'^info_card',     views.get_card,        name="get_card"),
    url(r'^blast',         views.blast,           name="blast"),
    url(r'^path_finder', views.path_finder,       name="path_finder"),
    url(r'^map_expression', views.map_expression, name="map_expression"),
    url(r'^tutorial', views.tutorial,             name="tutorial"),
    url(r'^show_connections', views.show_connections, name="show_connections"),
    url(r'^downloads', views.downloads, name="downloads"),
    url(r'^downloader', views.downloader, name="downloader"),
    url(r'^about', views.about, name="about"),
    url(r'^datasets', views.datasets, name="datasets"),
    url(r'^login', views.register, name="login"),
    url(r'^logout', views.logout_view, name="logout"),
    url(r'^account', views.account_view, name="account"),
    url(r'^experiment_summary', views.experiment_summary, name="experiment_summary"),
    url(r'^experiment_conditions', views.experiment_conditions, name="experiment_conditions"),
    url(r'^experiment_dge_table', views.experiment_dge_table, name="experiment_dge_table"),
    url(r'^experiment_dataset', views.experiment_dataset, name="experiment_dataset"),
    url(r'^plot_gene_expression', views.plot_gene_expression, name="plot_gene_expression"),
    url(r'^plot_tsne', views.plot_tsne, name="plot_tsne"),
    url(r'^experiment_condition_types', views.experiment_condition_types, name="experiment_condition_types"),
]
