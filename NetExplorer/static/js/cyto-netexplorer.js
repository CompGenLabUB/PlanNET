// Cytoscape style definition
var stylesheet = cytoscape.stylesheet()
    .selector('node')
        .css({
            'content': 'data(name)',
            'text-valign': 'center',
            'color': '#F8F8F8',
            'background-color': '#404040',
            'text-outline-width': 0.3,
            "font-size": 8,
            "text-outline-color": "#404040",
        })
    .selector('edge')
        .css({
            'width': 1,
            'line-color': 'data(colorEDGE)',
            'target-arrow-color': 'data(colorEDGE)'
        });



// Cytoscape variable definition
var cy = cytoscape({
    style: stylesheet,
    layout: { name: 'cose'},
    container: document.getElementById('cyt'),
    ready: function() {}
});


// Load graphelements from page
cy.load(graphelements);


// CHANGE LAYOUT CONTROLS
$('#select-layout li').on('click', function(){
    var newlayout = $(this).text().toLowerCase();
    cy.layout( { name: newlayout } )
});

$(".dropdown-menu li a").click(function(){
  $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
  $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
});



// Info card/expand on click
cy.nodes().on("click", function(){
    var card_data = {
        target  : this.data("name"),
        targetDB: this.data("database"),
        csrfmiddlewaretoken: '{{ csrf_token }}'
    }

    var behaviour = $('.click-behaviour:checked').val();

    if (behaviour == "on") { // True: card, False: expand
        // Get the ID of the div to update
        elementID = "card-overlay";
        $.ajax({
            type: "GET",
            url: "/info_card",
            data: {
                'target'    : card_data['target'],
                'targetDB'  : card_data['targetDB'],
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success : function(data) {
                $('[id="' + elementID + '"]').html(data);
                $('[id="card-overlay"]').slideToggle(450);
                $('.close-overlay').slideToggle(450);
                $('.full-screen-card').slideToggle(450);
            }
        });
    } else {
        alert("EXPAND");
    }



});



// CENTER TO CONTROLS

$("#center-to-graph").on("click", function(){
    cy.center();
});

$(".btn").mouseup(function(){
    $(this).blur();
})



// SAVE TO png

$("#save-image").on("click", function() {
    var graph_png = cy.png()
    $('#image-download').attr('href', graph_png);
});
