
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
            'target-arrow-shape': 'triangle',
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
    var newlayout = $(this).text();
    cy.layout( { name: newlayout } )
});
