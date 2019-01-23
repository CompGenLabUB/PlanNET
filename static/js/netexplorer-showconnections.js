// Functionality to show connections between nodes in graph

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

$("#show_connections").on("click", function(){
    var elements = get_graphelements(cy);

    $.ajax({
        type: "POST",
        url: window.ROOT + "/show_connections",
        cache: true,
        data: {
            'nodes': elements.node_ids,
            'databases': elements.databases,
            'csrfmiddlewaretoken': csrftoken
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
            filterByConfidence($('#sl1').val(), cy, $('input[name=show-plen]:checked').val());
            // Show or hide interactions depending on plen
            checkPlen($('input[name=show-plen]:checked').val(), cy, $('#sl1').val());
        },
        error : function(err) {
            $('#loading').hide();
            console.log(err);
        }
    });

});
