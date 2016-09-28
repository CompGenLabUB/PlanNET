
// Cytoscape style definition
var stylesheet = cytoscape.stylesheet()
    .selector('node')
        .css({
            'content': 'data(name)',
            'text-valign': 'center',
            'color': 'white',
            'background-color': 'data(colorNODE)',
            'text-outline-width': 2,
            'text-outline-color': 'data(colorNODE)'
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


// Change layout control
$('#select-layout li').on('click', function(){
    var newlayout = $(this).text().toLowerCase();
    cy.layout( { name: newlayout } )
});

$(".dropdown-menu li a").click(function(){
  $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
  $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
});



// Info card on click
cy.nodes().on("click", function(){
    var card_data = {
        target  : this.data("name"),
        targetDB: this.data("database"),
        csrfmiddlewaretoken: '{{ csrf_token }}'
    }


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


});
