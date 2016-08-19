from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.index_view, name='index_view'),
    url(r'^gene_searcher', views.gene_searcher, name="gene_searcher"),
]
