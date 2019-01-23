/* 
 * CYTOSCAPE EDITOR FOR PLANNET
 * ------------------------------------------------
 */




class CyEditor {
    constructor(containerId, cyInput=null, stylesheet=null) {

        if (! stylesheet) {
            console.log("No stylesheet...");
            var cyEditorStyle =  cytoscape.stylesheet()
                .selector('node[colorNODE]')
                    .css({
                        'content': 'data(name)',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'background-color': '#404040',
                        "font-size": 12,
                        'text-outline-width': 2,
                        "text-outline-color": "#FFFFFF",
                        "color": "#404040",
                        "border-color": "data(colorNODE)",
                        "border-width": 3,
                        "min-zoomed-font-size": 2,
                    })
                .selector('node[database = "Custom"]')
                    .css({
                        'border-color': "#ddadad",

                    })
                .selector('node[database = "Smest"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#bb4ab7",
                    })
                .selector('node[database = "Cthulhu"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#49b9d1",
                    })
                .selector('node[database = "Consolidated"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#74be47",
                    })
                .selector('node[database = "Dresden"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#ca552d",
            
                    })
                .selector('node[database = "Graveley"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#4b8c38",
                    })
                .selector('node[database = "Illuminaplus"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#b175e3",
                    })
                .selector('node[database = "Newmark"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#bcb042",
                    })
                .selector('node[database = "Smed454"]')
                    .css({
                        'shape': 'triangle',
                        'border-color': "#de9640",
            
                    })
                .selector('node[database = "Smedgd"]')
                    .css({
                        'shape': 'triangle',
                        'border-color': "#e4857b",
            
                    })
                .selector('node[database = "Adamidi"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#648ad0"
            
                    })
                .selector('node[database = "Blythe"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#d34057"
                    })
                .selector('node[database = "Pearson"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#5fc38f"
                    })
                .selector('node[database = "Gbrna"]')
                    .css({
                        'shape': 'circle',
                        'border-color': "#818941"
                    })
                .selector(':selected')
                    .css({
                        "background-color": "#d9534f",
                        "border-color": "#FDD4D4"
                    })
                .selector('edge')
                    .css({
                        'line-color': '#ddadad',
                        'target-arrow-color': '#ddadad',
                        'width': 3
                    })
                .selector('edge[colorEDGE]')
                    .css({
                        'line-color': 'data(colorEDGE)',
                        'target-arrow-color': 'data(colorEDGE)',
                        'width': 2
                    })
                .selector('.edgehandles-preview, .edgehandles-ghost-edge')
                    .css({
                        'line-color': '#ddadad',
                        'target-arrow-color': '#ddadad'
                    })
                .selector('.edgehandles-hover')
                    .css({
                        'background-color': '#ddadad'
                    })
                .selector('.edgehandles-handle')
                    .css({
                        'background-color': '#ddadad',
                        'color': '#ddadad'
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


        

        this.cytoscape.on("click", "node", function() {
            var clickBehaviour = $("input[value=on]:checked", ".editor-switch").closest("form").attr("id");
            alert(clickBehaviour);
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
                alert("REMOVING");
                this.remove();
            }
        });


        this.cytoscape.on("click", "edge", function() {
            var clickBehaviour = $("input[value=on]:checked", ".editor-switch").closest("form").attr("id");
            if (clickBehaviour == "editor-delete-interaction-form") {
                alert("EDGE");
                this.remove();
            }
        })


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
    
}

