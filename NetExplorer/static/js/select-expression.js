
$("#map-expression-btn").on("click", function(){
    $("#map-expression-dialog").slideToggle(250);
});

$("#close-map-expression").on("click", function(){
    $("#map-expression-dialog").hide();
});

$("#map-expression-btn-cancel").on("click", function(){
    $("#map-expression-dialog").hide();
});


$("#map-expression-error").hide();


// Function to change the colors of the nodes depending on expression files


$("#map-expression-btn-submit").on("click", function(){
    var elements   = get_graphelements(cy);
    var experiment = $("#select-expression").val();
    var sample     = $("#select-sample").val();
    var type       = $('.active').attr('id');
    var ERRORTIME  = 3000;
    if (type === "two-sample") {
        if (! $("#select-sample1").val() || ! $("#select-sample2").val()) {
            // One of the two samples missing in two-sample mode!
            sample = "";
        } else {
            sample = $("#select-sample1").val() + ":" + $("#select-sample2").val();
        }
    }

    if (! experiment) {
        $("#map-expression-error-msg").html("No Experiment selected");
        $('#map-expression-error').slideToggle(200);
        setTimeout(function () {
            $('#map-expression-error').hide(200);
        }, ERRORTIME);
    } else if (! sample) {
        $("#map-expression-error-msg").html("No Sample selected");
        $('#map-expression-error').slideToggle(200);
        setTimeout(function () {
            $('#map-expression-error').hide(200);
        }, ERRORTIME);
    } else if (! elements.node_ids) {
        $("#map-expression-error-msg").html("No Nodes in graph");
        $('#map-expression-error').slideToggle(200);
        setTimeout(function () {
            $('#map-expression-error').hide(200);
        }, ERRORTIME);
    } else {
        $.ajax({
            type: "GET",
            url: "/map_expression",
            cache: true,
            data: {
                'experiment': $("#select-expression").val(),
                'sample'    : sample,
                'type'      : type,
                'nodes'     : elements.node_ids,
                'databases' : elements.databases,
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
    }



});
