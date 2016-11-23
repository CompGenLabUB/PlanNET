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
