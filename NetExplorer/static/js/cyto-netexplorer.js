$(document).ready(function(){
    if (upload_json) {
        cy.add(upload_json);
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
        checkHomologs(this);
    });

    // Add node text form
    $("#add_node").submit(function(e) {
        var formObj = {};
        var dataArray = $("#add_node").serializeArray(),
        dataObj = {};
        $(dataArray).each(function(i, field){
            dataObj[field.name] = field.value;
        });
        addNode(dataObj.genesymbol, dataObj.database);
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
        } else if (behaviour == "expand") {
            node.data("colorNODE", '#449D44');
            addNode(card_data['target'], card_data['targetDB']);
        } else if (behaviour == "delete") {
            node.remove();
        }

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
        var jsonGraph = JSON.stringify(cy.json()['elements']);
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
                "Delete graph": function() {
                    cy.nodes().remove();
                    $( this ).dialog( "close" );
                },
                Cancel: function() {
                    $( this ).dialog( "close" );
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
