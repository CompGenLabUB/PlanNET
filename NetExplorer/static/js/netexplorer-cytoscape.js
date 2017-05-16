// This script contains the general behaviour of the NetExplorer application.
// It uses several other scripts that can also be found in the js/ folder.


$(document).ready(function(){
    if (upload_json) {
        cy.add(upload_json);
        countNodes(cy);
        if (no_layout) {
            cy.layout({
                name: 'cola',
                maxSimulationTime: 3000,
                fit: true,
                directed: false,
                padding: 40
            });
        }
    }

    // CHANGE LAYOUT CONTROLS
    $('#select-layout li').on('click', function(){
        var newlayout = $(this).text().toLowerCase();
        cy.layout( { name: newlayout } );
    });

    $(".dropdown-menu li a").click(function(){
      $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
      $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
    });

    // Show homologs toggle
    $('#show-homologs').change(function () {
        checkHomologs(this, cy);
    });

    // Add node text form
    $("#add_node").submit(function(e) {
        var formObj = {};
        var dataArray = $("#add_node").serializeArray(),
        dataObj = {};
        $(dataArray).each(function(i, field){
            dataObj[field.name] = field.value;
        });
        addNode(dataObj.genesymbol, dataObj.database, cy);
        e.preventDefault(); // avoid to execute the actual submit of the form.
    });

    // Info card/expand on click
    cy.on( 'click', 'node', function() {
         // Change color of clicked node
        node = this;
        var card_data = {
            target  : this.data("name"),
            targetDB: this.data("database"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        };

        var behaviour = $('input[name=behaviour]:checked', '#behaviour-form').val();

        if (behaviour == "card") {
            // Get the ID of the div to update
            getCard(card_data);
        } else if (behaviour == "expand" && node.data("database") != "Human") {
            $("#expand-node-degree").html(node.data("degree"));
            if (node.data("degree") >= 100) {
                $( "#dialog-expand-node" ).dialog({
                    resizable: false,
                    height: "auto",
                    width: 400,
                    modal: true,
                    buttons: {
                        Cancel: function() {
                            $( this ).dialog( "close" );
                        },
                        "Expand node": function() {
                            node.data("colorNODE", '#449D44');
                            addNode(card_data.target, card_data.targetDB, cy);
                            $( this ).dialog( "close" );
                        }
                    }
                });
            } else {
                node.data("colorNODE", '#449D44');
                addNode(card_data.target, card_data.targetDB, cy);
            }


        } else if (behaviour == "delete") {

            $( "#dialog-delete-node" ).dialog({
                resizable: false,
                height: "auto",
                width: 400,
                modal: true,
                buttons: {
                    Cancel: function() {
                        $( this ).dialog( "close" );
                    },
                    "Delete node": function() {
                        node.remove();
                        countNodes(cy);
                        $( this ).dialog( "close" );
                    }
                }
            });


        }

    });


    // MOUSEOVER ON NODES
    cy.on('mouseover', 'node', function (evt) {
        $('html,body').css('cursor', 'pointer');
        this.css("opacity", "0.85");
    } );

    cy.on('mouseout', 'node', function (evt) {
        $('html,body').css('cursor', 'default');
        this.css("opacity", "1");
    });



    // FILTER edges with probability below threshold
    $('#sl1').slider().on('slideStop', function(ev){
        //var value = $('#sl1').slider('getValue');
        var value = $('#sl1').val();
        cy.filter(function(i, element){
            if ( element.isEdge() ) {
                if( element.data("probability") >= value ){
                    element.show();
                    return true;
                }
                element.hide();
            }
            // Not an edge
        });


    });



    // CYTOSCAPE CONTROLS

    $(".btn").mouseup(function(){
        $(this).blur();
    });

    // Center graph
    $("#center-to-graph").on("click", function(){
        cy.center();
        cy.fit();
    });


    // Save png

    $("#save-image").on("click", function() {
        var graph_png = cy.png();
        $('#save-image-link').attr('href', graph_png);
    });


    // Export TBL
    $("#export-tbl").on("click", function(){
        var jsonGraph = cy.json().elements;
        var nodes     = {};
        var edges     = {};
        for (var key in jsonGraph.nodes) {
            var node = jsonGraph.nodes[key].data.id;
            nodes[node] = 1;
        }
        nodes = Object.keys(nodes).join("\n"); // to string

        for (var ekey in jsonGraph.edges) {
            var edge = jsonGraph.edges[ekey].data.id;
            edge = edge.replace("-", "\t");
            edge = edge + "\t" + jsonGraph.edges[ekey].data.probability;
            edges[edge] = 1;
        }
        edges = Object.keys(edges).join("\n"); // to string
        tblString = nodes + "\n" + edges;
        var blob = new Blob([tblString], {type: "text/plain;charset=utf-8"});
        saveAs(blob, "graph-export.tbl");
    });


    // Save Graph
    $("#save-graph").on("click", function(){
        var jsonGraph = JSON.stringify(cy.json().elements);
        var blob = new Blob([jsonGraph], {type: "text/plain;charset=utf-8"});
        saveAs(blob, "graph-export.json");
    });


    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Delete All
    $("#delete-all").on("click", function() {
        $( "#dialog-confirm" ).dialog({
            resizable: false,
            height: "auto",
            width: 400,
            modal: true,
            buttons: {
                Cancel: function() {
                    $( this ).dialog( "close" );
                },
                "Delete graph": function() {
                    cy.nodes().remove();
                    countNodes(cy);
                    $( this ).dialog( "close" );
                    $('#color-gradient').hide();
                }
            }
        });

    });


    // Initialize slider when loading page.
    $('#sl1').slider().slider('setValue', 0.6);

    // Behaviour when on click
    $("#remove-unconnected").on("click", function() {
        // Remove unconnected nodes
        $( "#dialog-unconnected" ).dialog({
            resizable: false,
            height: "auto",
            width: 400,
            modal: true,
            buttons: {
                Cancel: function() {
                    $( this ).dialog( "close" );
                },
                "Delete nodes": function() {
                    var slider_value = $('#sl1').val();
                    if (! slider_value) {
                        slider_value = 0.6;
                    }
                    $( this ).dialog( "close" );
                    cy.filter(function(i, element){
                        if ( element.isNode() ) {
                            var selector = "[probability>=" + slider_value + "]";
                            var edge_collection = element.connectedEdges(selector);
                            if (! edge_collection.data()) {
                                cy.remove(element);
                                countNodes(cy);
                            }
                        }
                    });
                }
            }
        });

    });


    $('#node-not-found').hide();


    $( "#dialog-jsonerr" ).dialog({
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        buttons: {
            "Close": function() {
                $( this ).dialog( "close" );
            }
        }
    });


});

// Function that returns the nodes and the databases of the elements in the graph
// used in select-expression.js and netexplorer-showconnections.js
function get_graphelements(cy) {
    var nodes     = cy.elements('node[database != "Human"]');
    var node_ids  = [];
    var databases = [];
    for (var i = 0; i < nodes.length; i++) {
        node_ids.push( nodes[i].data("id") );
        databases.push( nodes[i].data("database") );
    }
    var data = {};
    data.node_ids = node_ids.join(",");
    data.databases = databases.join(",");
    return data;
}
