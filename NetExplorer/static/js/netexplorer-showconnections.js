$("#show_connections").on("click", function(){
    var nodes     = cy.elements('node[database != "Human"]');
    var node_ids  = [];
    var databases = [];
    for (var i = 0; i < nodes.length; i++) {
        node_ids.push( nodes[i].data("id") );
        databases.push( nodes[i].data("database") )
    }
    node_ids  = node_ids.join(",");
    databases = databases.join(",");

    $.ajax({
        type: "GET",
        url: "/show_connections",
        cache: true,
        data: {
            'nodes': node_ids,
            'databases': databases,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        success : function(data) {
            var newelements = cy.add(data);

            // Layout graph so that everything appears
            cy.layout({
                name: 'cola',
                maxSimulationTime: 3000,
                fit: true,
                directed: false,
                padding: 40
            });

            // Show only edges above slider threshold
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
        },
        error : function(err) {
            console.log(err);
        }
    });

});
