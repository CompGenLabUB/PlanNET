
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

$(".pick-color-group").on("click", function() {
    $(".pick-color-group.group-selected").removeClass("group-selected");
    $(this).addClass("group-selected");
});

var hexDigits = new Array
        ("0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f");


function hex(x) {
  return isNaN(x) ? "00" : hexDigits[(x - x % 16) / 16] + hexDigits[x % 16];
 }

//Function to convert rgb color to hex format
function rgb2hex(rgb) {
    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    return "#" + hex(rgb[1]) + hex(rgb[2]) + hex(rgb[3]);
}

$("#map-expression-btn-submit").on("click", function(){
    var elements   = get_graphelements(cy);
    var experiment = $("#select-expression").val();
    var sample     = $("#select-sample").val();
    var color      = $(".pick-color-group.group-selected .pick-color-select-color").css("background-color");
    color          = rgb2hex(color);
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
                'color'     : color,
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
                        var percentile = (100 - (bin * 5));
                        //var next;
                        //if (bin == sorted_keys.length - 1) {
                        //    // Last element!
                        //    next = 0;
                        //} else if (bin == 0) {
                        //    // First element
                        //    previous = "+";
                        //    next     = sorted_keys[bin];
                        //} else {
                        //    // Not last element
                        //    next = sorted_keys[bin];
                        //}
                        gradient_html += "<tr><td class='color-gradient-td-color' bgcolor='" +
                                         experiment.gradient[sorted_keys[bin]] + "'>&nbsp</td><td class='color-gradient-td'> " +
                                         percentile + "%" + "</td></tr>";

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
                alert("AJAX ERROR");
                $('#loading').hide();
            }
        });
    }



});
