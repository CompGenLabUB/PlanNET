
$("#map-expression-btn").on("click", function(){
    $("#map-expression-dialog").slideToggle(250);
});

$("#close-map-expression").on("click", function(){
    $("#map-expression-dialog").hide();
});

$("#map-expression-btn-cancel").on("click", function(){
    $("#map-expression-dialog").hide();
});


// Function to change the colors of the nodes depending on expression files


$("#map-expression-btn-submit").on("click", function(){
    var elements = get_graphelements(cy);
    $.ajax({
        type: "GET",
        url: "/map_expression",
        cache: true,
        data: {
            'experiment': $("#select-expression").val(),
            'sample': $("#select-sample").val(),
            'nodes': elements.node_ids,
            'databases': elements.databases,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        beforeSend: function() {
            $('#loading').show();
        },
        success : function(data) {
            $('#loading').hide();
            $('#map-expression-dialog').slideToggle(250);
            // Change cytoscape node colors
        },
        error : function(err) {
            $('#loading').hide();
        }
    });
});
