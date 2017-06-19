// Functionality to show connections between nodes in graph

$("#show_connections").on("click", function(){
    var elements = get_graphelements(cy);

    $.ajax({
        type: "GET",
        url: "/PlanNET/show_connections",
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
            var to_show_selector = "edge[probability>=" + value + "]";
            var to_hide_selector = "edge[probability<" + value + "]";
            cy.elements(to_show_selector).show();
            cy.elements(to_hide_selector).hide();
            // Show or hide interactions depending on plen
            checkPlen($('input[name=show-plen]:checked').val(), cy);
        },
        error : function(err) {
            $('#loading').hide();
            console.log(err);
        }
    });

});
