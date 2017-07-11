// FUNCTIONS TO SHOW HOMOLOG NODES IN CYTOSCAPE

function displayHomologs(cyobj) {
    // Function to get the Homologs of each node and add them to "cy"
    var elementsToAdd = {"nodes": [], "edges": []};
    cyobj.filter(function(i, element){
        if ( element.isNode() ) {
            var nodeId  = element.data("id");
            var homolog = element.data("homolog");
            if (homolog) {
                var homologElement = { "data" : {id: homolog, database: "Human", name: homolog, colorNODE: "#6785d0" } };
                var homologyEdge   = { "data" : { id: homolog + "-" + nodeId, probability: 1, source: homolog, target: nodeId , type: "homology", colorEDGE: "#6785d0"} };
                elementsToAdd.nodes.push(homologElement);
                elementsToAdd.edges.push(homologyEdge);
            }
        }
    });

    cyobj.filter(function(i, element){
        if ( element.isEdge() ) {
            if (! element.data("type")) {
                // Not an homology edge
                var selector_1 = 'node[id = "' + element.data("source") + '"]';
                var selector_2 = 'node[id = "' + element.data("target") + '"]';
                var source = cy.filter(selector_1);
                var target = cy.filter(selector_2);
                if (element.data("pathlength") == 1) {
                    var homologIntEdge   = { "data" : { id: source.data("homolog") + "-" + target.data("homolog"), type: "homologyInt", probability: 1, source: source.data("homolog"), target: target.data("homolog") , colorEDGE: "#6785d0"} };
                    elementsToAdd.edges.push(homologIntEdge);
                }
            }

        }
    });
    var added = cyobj.add(elementsToAdd);
    var layout = added.makeLayout({
        name: 'grid'
    });
    layout.run();

    //added.layout({
    //    name: 'cola',
    //    maxSimulationTime: 3000,
    //    fit: true,
    //    directed: false,
    //    padding: 40
    //});
}


function checkHomologs(toggle, cyobj) {
    // This is a checker function to see if the toggle is on or off and call the
    // above function if needed or to remove the homologs.
    if(toggle.checked) {
        displayHomologs(cyobj);
    } else {
        var toRemove = cyobj.elements('node[database = "Human"]');
        cyobj.remove( toRemove );
    }
}


function checkPlen(value, cyobj, confvalue) {
    if (value == "show") {
        var show_selector = "edge[pathlength=2]" + "[probability>=" + confvalue + "]";
        cyobj.elements(show_selector).show();
    } else {
        cyobj.elements("edge[pathlength=2]").hide();
    }
}
