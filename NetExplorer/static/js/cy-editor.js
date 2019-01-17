/* 
 * CYTOSCAPE EDITOR FOR PLANNET
 * ------------------------------------------------
 */




class CyEditor {
    constructor(containerId, cyInput=null, stylesheet=null) {

        if (! stylesheet) {
            console.log("No stylesheet...");
            var cyEditorStyle =  cytoscape.stylesheet()
                .selector('node')
                    .css({
                        'content': 'data(name)',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'background-color': '#404040',
                        "font-size": 12,
                        'text-outline-width': 2,
                        "text-outline-color": "#FFFFFF",
                        "color": "#404040",
                        ////"border-color": "data(colorNODE)",
                        "border-width": 2,
                        "min-zoomed-font-size": 2,
                    })
                .selector('node[database = "Custom"]')
                    .css({
                        'background-color': "#FDD4D4",
                    })
                .selector(':selected')
                    .css({
                        "background-color": "#d9534f",
                        "border-color": "#FDD4D4"
                    })
                .selector('edge')
                    .css({
                        //'line-color': 'data(colorEDGE)',
                        //'target-arrow-color': 'data(colorEDGE)'
                    })
                ;
        }


        var that = this;
        this.cytoscape = cytoscape({
            container: document.getElementById(containerId),
            elements: JSON.parse(JSON.stringify(cyInput.elements().jsons())),
            layout: { name: 'preset' },
            positions: cyInput.nodes().positions(),
            wheelSensitivity: 0.25,
            style: cyEditorStyle
        });


        var clickBehaviour = $("input[value=on]:checked", ".editor-switch").closest("form").attr("id");

        this.cytoscape.on("click", "node", function() {
            if (clickBehaviour == "editor-interaction-form") {
                /*
                // Check if there is a node already selected
                var selectedNode = that.cytoscape.nodes(":selected");
                if (selectedNode.length == 1) {
                    that.addInteraction(selectedNode, this);
                    that.cytoscape.nodes().unselect();
                } else {
                    console.log("No selected node...");
                }
                */
            } else if (clickBehaviour == "editor-delete-node-form") {
                this.remove();
            }
        });

        /*
        this.cytoscape.on("click", "edge", function() {
            if (clickBehaviour == "editor-delete-interaction-form") {
                this.remove();
            }
        })
        */

    }

    runLayout() {
        this.cytoscape.layout({
            name: 'cola',
            maxSimulationTime: 3000,
            fit: true,
            directed: false,
            padding: 40
        });
    }

    addNode(name, homolog) {
        var error = null;
        if (!name) {
            error = "Name must be provided.";
            return error;
        }

        var json_data = { 
            'nodes': [ 
                {
                    'data': { 
                        'id': name, 'name': name, 'database': 'Custom', 'colorNODE': "#404040" 
                    },
                }
            ] 
        };
        if (homolog) {
            json_data.nodes[0].data.homolog = homolog;
        };

        this.cytoscape.add(json_data);
        this.runLayout();
    }

    
    addInteraction(node1, node2) {
        var json_data = {
            'edges': [
                {
                    'data': {
                        'id': node1.data("name") + "-" + node2.data("name"),
                        'source': node1.data("name"),
                        'target': node2.data("name"),
                        //'colorEDGE': "#019dcc"
                    }
                }
            ]
        }

        this.cytoscape.add(json_data);
        this.runLayout();

    }
    
}

