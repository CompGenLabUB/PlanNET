// ADD NODE WHEN CLICKING ON NODE IN CYTOSCAPE JS
// Function to check if the toggle "show homologs is On or Off and do whatever needs to be done"

function addNode(symbol, database) {
    // This function takes a symbol and a database and adds the node neighbour nodes
    // to the cytoscape object. IT does an ajax request to net_explorer to get the
    // neighbours as a JSON object.
    $.ajax({
        type: "GET",
        url: "/net_explorer",
        cache: true,
        data: {
            'genesymbol': symbol,
            'database'  : database,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        success : function(data) {
            var layout_name = $('#select-layout li').text().toLowerCase();
            var newelements = cy.add(data);
            checkHomologs(document.getElementById( "show-homologs" )); // Show homologs if necessary

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
        error : function() {
            $('#node-not-found').slideToggle(200);
            setTimeout(function () {
                $('#node-not-found').hide(200);
            }, 2000);
        }

    });
}
