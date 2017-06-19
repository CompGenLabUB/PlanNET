// ADD NODE WHEN CLICKING ON NODE IN CYTOSCAPE JS
// Function to check if the toggle "show homologs is On or Off and do whatever needs to be done"

function loadJsonGraph(data, cyobj) {
    // Function that takes the json and the cyobj and loads the graph
    var newelements = cyobj.add(data);
    checkHomologs(document.getElementById( "show-homologs" ), cyobj); // Show homologs if necessary

    cyobj.layout({
        name: 'cola',
        maxSimulationTime: 3000,
        fit: true,
        directed: false,
        padding: 40
    });
    $('#loading').hide();

    // Show only edges above slider threshold
    var value = $('#sl1').val();
    cyobj.filter(function(i, element){
        if ( element.isEdge() ) {
            if( element.data("probability") >= value ){
                element.show();
                return true;
            }
            element.hide();
        }
        // Not an edge
    });
    // Show or hide edges depending on plen
    checkPlen($('input[name=show-plen]:checked').val(), cyobj);
    countNodes(cyobj);
}

function addNode(symbol, database, type, cyobj) {
    // This function takes a symbol and a database and adds the node's neighbour nodes
    // to the cytoscape object. It does an ajax request to net_explorer to get the
    // neighbours as a JSON object.
    $.ajax({
        type: "GET",
        url: "/net_explorer",
        cache: true,
        data: {
            'genesymbol': symbol,
            'database'  : database,
            'type'      : type,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        beforeSend: function() {
            $('#loading').show();
        },
        success : function(data) {
            var layout_name = $('#select-layout li').text().toLowerCase();
            if (data.nodes.length >= 100) {
                // You are adding too many nodes, ask before adding nodes
                $("#toomany-number").html(data.nodes.length);

                $( "#dialog-toomany" ).dialog({
                    resizable: false,
                    height: "auto",
                    width: 400,
                    modal: true,
                    close: function( event, ui ) {
                        $( this ).dialog( "close" );
                        $('#loading').hide();
                        return;
                    },
                    buttons: {
                        Cancel: function() {
                            $( this ).dialog( "close" );
                            $('#loading').hide();
                            return;
                        },
                        "Add nodes": function() {
                            loadJsonGraph(data, cyobj);
                            $( this ).dialog( "close" );
                            $('#loading').hide();
                        }
                    }
                });
            } else {
                // Add nodes no matter what
                loadJsonGraph(data, cyobj);
                $('#loading').hide();
            }
        },
        statusCode: {
            404: function () {
                $('#loading').hide();
                $('.node-not-found-err').html("Node not found");
                $('#node-not-found').show();
                setTimeout(function () {
                    $('#node-not-found').hide(200);
                }, 2000);
            },
            400: function () {
                $('#loading').hide();
                $('.node-not-found-err').html("Bad Request");
                $('#node-not-found').show();
                setTimeout(function () {
                    $('#node-not-found').hide(200);
                }, 2000);
            },
        },
        error : function() {
            $('#loading').hide();
            $('.node-not-found-err').html("Server Error");
            $('#node-not-found').show();
            setTimeout(function () {
                $('#node-not-found').hide(200);
            }, 2000);
        },

    });
}
