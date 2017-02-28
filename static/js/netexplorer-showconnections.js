// Functionality to show connections between nodes in graph

$("#show_connections").on("click", function(){
    var elements = get_graphelements(cy);

    $.ajax({
        type: "GET",
        url: "/show_connections",
        cache: true,
        data: {
            'nodes': elements.node_ids,
            'databases': elements.databases,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        beforeSend: function() {
            $('#loading').show();
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
            $('#loading').hide();

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
            $('#loading').hide();
            console.log(err);
        }
    });

});
