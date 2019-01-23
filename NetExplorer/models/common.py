from __future__ import unicode_literals
from django.db import models
from py2neo import Graph
from  django.contrib.auth.models import User
import json
import logging
from colour import Color
import math
import re
import time
from django.db import connection
import requests
from wsgiref.util import FileWrapper
import tempfile
from django.http        import HttpResponse
import os
from django.http  import HttpResponse
from wsgiref.util import FileWrapper
import tempfile

GRAPH     = Graph("http://127.0.0.1:7474/db/data/")
DATABASES = set([
    "Dresden",
    "Consolidated",
    "Smest",
    #"Newmark",
    "Graveley",
    "Illuminaplus",
    "Smed454",
    "Smedgd",
    "Adamidi",
    "Blythe",
    "Pearson",
    "Gbrna",
])

ALL_DATABASES = set([
    "Dresden",
    "Consolidated",
    #"Newmark",
    "Graveley",
    "Smest",
    "Illuminaplus",
    "Smed454",
    "Smedgd",
    "Adamidi",
    "Blythe",
    "Pearson",
    'Cthulhu',
    "Gbrna",
])


# UTILITIES
def query_node(symbol, database):
    '''
    This simple function takes a symbol and a database and tries to get it from
    the DB
    '''
    node   = None
    symbol = symbol.replace(" ", "")
    symbol = symbol.replace("'", "")
    symbol = symbol.replace('"', '')
    symbol = symbol.replace("%7C", "|")
        # Urls in django templates are double encoded for some reason
        # Because we have identifiers with '|' symbols, they get encoded to %257, that gets decodeed
        # to %7C. I have to re-decode it to '|'

    if database == "Human":
        symbol = symbol.upper()
        node = HumanNode(symbol, database)
    else:
        node = PlanarianContig(symbol, database)
        node.get_summary()
    return node

from NetExplorer.models.neo4j_models import *