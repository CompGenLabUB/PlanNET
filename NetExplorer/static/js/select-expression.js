// Behaviour of the map expression dialog
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

// -----------------------
// Choose colors for the gradient when click on color div
$(".pick-color-group").on("click", function() {
    $(".pick-color-group.group-selected").removeClass("group-selected");
    $(this).addClass("group-selected");
});

//------------------------
// Form management
$(".sample-option").hide();
$("#select-expression").on("change", function(){
    $(".sample-option").hide();
    $(".sample-warning").hide();
    var to_show = ".sample-option." + $("#select-expression").val();
    $(to_show).show();
});

// -----------------------
// Transform from rgb to hex
var hexDigits = new Array
        ("0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f");
function hex(x) {
  return isNaN(x) ? "00" : hexDigits[(x - x % 16) / 16] + hexDigits[x % 16];
 }
function rgb2hex(rgb) {
    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    return "#" + hex(rgb[1]) + hex(rgb[2]) + hex(rgb[3]);
}

// -----------------------
// Select default color when clicking on one-sample or two-sample
$("#one-sample-toggle").on("click", function(){
    $(".pick-color-group.group-selected").removeClass("group-selected");
    $(".default-1").addClass("group-selected");
});
$("#two-sample-toggle").on("click", function(){
    $(".pick-color-group.group-selected").removeClass("group-selected");
    $(".default-2").addClass("group-selected");
});

// -----------------------
/*
    Function that gets expression data from DB, calling the view map_expression
    through an AJAX request. It will receive a JSON with all the data needed to
    change the color of the nodes depending on the expression and to create the
    legend for the expression.

    Object:
        "experiment":
            "gradient":
                "bin1": "color",
                "bin2": "color"
                ...
            "maxexp": num
            "minexp": num
            "reference": "string"
        "expression":
            "symbol": "color"
            ...
        "status": "something"
        "type": "one-sample" | "two-sample"
*/
$("#map-expression-btn-submit").on("click", function(){
    var elements   = get_graphelements(cy);
    var experiment = $("#select-expression").val();
    var sample     = $("#select-sample").val();
    var from_color = $(".pick-color-group.group-selected .pick-color-select-fromcolor").css("background-color");
    var to_color   = $(".pick-color-group.group-selected .pick-color-select-tocolor").css("background-color");
    from_color = rgb2hex(from_color);
    to_color   = rgb2hex(to_color);
    var type       = $('.active').attr('id');
    var ERRORTIME  = 3000;
    if (type === "two-sample") {
        if (! $("#select-sample1").val() || ! $("#select-sample2").val()) {
            // One of the two samples missing in two-sample mode!
            sample = "";
        } else {
            if ($("#select-sample1").val() == $("#select-sample2").val()) {
                $("#map-expression-error-msg").html("Please, select different samples.");
                $('#map-expression-error').slideToggle(200);
                setTimeout(function () {
                    $('#map-expression-error').hide(200);
                }, ERRORTIME);
                return;
            } else {
                sample = $("#select-sample1").val() + ":" + $("#select-sample2").val();
            }
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
                'experiment' : $("#select-expression").val(),
                'sample'     : sample,
                'type'       : type,
                'from_color' : from_color,
                'to_color'   : to_color,
                'nodes'      : elements.node_ids,
                'databases'  : elements.databases,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            beforeSend: function() {
                $('#loading').show();
            },
            success : function(data) {
                $('#loading').hide();
                if (data.status === "no-expression") {
                    $("#map-expression-error-msg").html("No expression available for nodes in graph");
                    $('#map-expression-error').slideToggle(200);
                    setTimeout(function () {
                        $('#map-expression-error').hide(200);
                    }, ERRORTIME);
                } else {
                    // At least one node has expression
                    // Change cytoscape node colors
                    var expression = jQuery.parseJSON(data.expression);
                    var experiment = jQuery.parseJSON(data.experiment);
                    $('#map-expression-dialog').slideToggle(250);
                    // Iterate through nodes
                    cy.filter(function(i, element){
                        if ( element.isNode() && element.data("database") != "Human") {
                            if (element.data("id") in expression) {
                                element.css("background-color", expression[element.data("id")]);
                            } else {
                                element.css("background-color", "#404040");
                            }
                        }
                    });
                    var gradient_html = "<div id='gradient-title'> <h4>" + experiment.id + "<h4>" +
                                            "<h6><i class='subtitle'>" + experiment.reference + "</i></h6>";
                    gradient_html += "<table id='color-gradient-table'>";
                    console.log(data);
                    console.log(experiment);
                    var sorted_keys = Object.keys(experiment.gradient).sort(function(a,b) { return b - a; } );
                    var previous = sorted_keys[0];
                    for (var bin in sorted_keys) {
                        var percentile;
                        if (data.type == "one-sample") {
                            percentile = (100 - (bin * 5)) + "%";
                        } else {
                            percentile = sorted_keys[bin];
                        }
                        gradient_html += "<tr><td class='color-gradient-td-color' bgcolor='" +
                                         experiment.gradient[sorted_keys[bin]] + "'>&nbsp</td><td class='color-gradient-td'> " +
                                         percentile + "</td></tr>";

                    }
                    gradient_html += `<tr>
                                        <td class='color-gradient-td-color-empty' bgcolor='white'>
                                            &nbsp
                                        </td>
                                        <td class='color-gradient-td'>
                                            &nbsp
                                        </td>
                                      </tr>
                                      <tr>
                                        <td class='color-gradient-td-color' bgcolor='#404040'>
                                            &nbsp
                                        </td>
                                        <td class='color-gradient-td'>
                                            NA
                                        </td>
                                      </tr>
                    `;
                    gradient_html += "</table></div>";
                    $('#color-gradient').html(gradient_html);
                    $('#color-gradient').hide();
                    $('#color-gradient').slideToggle(250);
                }
            },
            error : function(err) {
                $('#loading').hide();
            }
        });
    }

});
