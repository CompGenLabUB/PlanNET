// CYTOSCAPE DEFINITION FOR NET EXPLORER

// Cytoscape style definition
var stylesheet = cytoscape.stylesheet()
    .selector('node')
        .css({
            'content': 'data(name)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'background-color': 'data(colorNODE)',
            "font-size": 8,
            'text-outline-width': 2,
            "text-outline-color": "#FFFFFF",
            "color": "#404040",
            "border-color": "#404040",
            "border-width": 1,
        })
    .selector('edge')
        .css({
            'content': 'data(probability)',
            'font-size': 6,
            'width': 1,
            'color': "#404040",
            'text-background-opacity': 1,
            'text-background-color': '#F8F8F8',
            'text-background-shape': 'roundrectangle',
            'text-border-color': '#404040',
            'text-border-width': 0.1,
            'text-border-opacity': 0.5,
            'line-color': 'data(colorEDGE)',
            'target-arrow-color': 'data(colorEDGE)'
        })
    .selector('edge[type = "homology"]')
        .css({
            'line-style': 'dashed',
            'content': '',
            'opacity': 0.8
        })
    .selector('edge[type = "homologyInt"]')
        .css({
            'content': '',
            'opacity': 0.8
        })
    .selector('node[database = "Cthulhu"]')
        .css({
            'shape': 'circle',
        })
    .selector('node[database = "Consolidated"]')
        .css({
            'shape': 'triangle',
        })
    .selector('node[database = "Dresden"]')
        .css({
            'shape': 'pentagon',
        })
    .selector('node[database = "Human"]')
        .css({
            'shape': 'diamond',
        });


// Cytoscape variable definition
var cy = cytoscape({
    style: stylesheet,
    layout: { name: 'preset' },
    container: document.getElementById('cyt'),
    ready: function() {}
});
