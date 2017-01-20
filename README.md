# PlaNET
Django web application to explore gene/protein interactions of Schmidtea mediterranea.

# Version
v0.1.0

# Description
Application to explore the different Schmidtea mediterranea predicted interactomes. 

## NetExplorer/models.py
>In this file we can find the models for this application. The models are, basically, the classes used
by the app, such as the "PredictedNode" class and "GraphCytoscape" class. All the queries to the DB are done
through here, as well as the connection to the Neo4j database. It basically contains the "logic" of the application.
Do not change the interface of any of the classes, or everything will be DESTROYED.

## NetExplorer/views.py
>This file contains the part of the application that decides "what" to display. All the requests "GET/POST" ajax or otherwise
are handled here. It imports the models.py file and uses the classes defined there to choose what to display to the user. Because
I am a very bad programmer, some of the logic of the application is located here, BUT that should not be the case, so if you decide to expand on the application, try to be better than me and do not put app logic here. Every view function returns either an http response with some text (usually json) or a call to the template renderer.

## NetExplorer/templates/
> Here we can find the HTML of the different pages of the application. All of them are called by views.py's functions. The templates decide "HOW" to display the data chosen by the views.py function. Try not to put logic here either.

## NetExplorer/static/js
> All the javascript files are located here. Because the app uses many ajax request and interactivity, a lot of the logic of the app is located in these scripts. Some of them will only work with DOMS (deciding how they should behave), while others will make requests to views.py functions and get a json response (and then work with it). All the cytoscape.js code is located here.

## NetExplorer/static/css
> Stylesheets

## NetExplorer/static/Images
> Images



# Authors
Sergio Castillo-Lara

# Copyright
