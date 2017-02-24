
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
            url: "/PlanNET/map_expression",
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
                if (data.status === "no-expression") {
                    alert("No Expression response");
                    $("#map-expression-error-msg").html("No expression available for nodes in graph");
                    $('#map-expression-error').slideToggle(200);
                    setTimeout(function () {
                        $('#map-expression-error').hide(200);
                    }, ERRORTIME);
                } else {
                    // At least one node has expression
                    // Change cytoscape node colors
                    console.log(data);
                    var expression = jQuery.parseJSON(data.expression);
                    $('#map-expression-dialog').slideToggle(250);
                    // Iterate through nodes
                    cy.filter(function(i, element){
                        if ( element.isNode() && element.data("database") != "Human") {
                            if (element.data("id") in expression) {
                                element.css("background-color", expression[element.data("id")])
                            } else {
                                element.css("background-color", "#404040")
                            }
                        }
                    });
                    console.log(data);
                }
            },
            error : function(err) {
                alert("AJAX ERROR");
                $('#loading').hide();
            }
        });
    }



});
