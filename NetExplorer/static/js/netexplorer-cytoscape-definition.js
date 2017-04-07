// CYTOSCAPE DEFINITION FOR NET EXPLORER

// Cytoscape style definition
var stylesheet = cytoscape.stylesheet()
    .selector('node')
        .css({
            'content': 'data(name)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'background-color': '#404040',
            "font-size": 8,
            'text-outline-width': 2,
            "text-outline-color": "#FFFFFF",
            "color": "#404040",
            "border-color": "data(colorNODE)",
            "border-width": 2,
            "min-zoomed-font-size": 6,
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
            'target-arrow-color': 'data(colorEDGE)',
            "min-zoomed-font-size": 6,
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
    .selector('node[database != "Human"]')
        .css({
            'width': 'mapData(degree, 1, 200, 10, 30)',
            'height': 'mapData(degree, 1, 200, 10, 30)',
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
    .selector('node[database = "Graveley"]')
        .css({
            'shape': 'vee',
        })
    .selector('node[database = "Illuminaplus"]')
        .css({
            'shape': 'rhomboid',
        })
    .selector('node[database = "Newmark"]')
        .css({
            'shape': 'hexagon',
        })
    .selector('node[database = "Smed454"]')
        .css({
            'shape': 'rectangle',
        })
    .selector('node[database = "Human"]')
        .css({
            'width': 20,
            'height': 20,
            'shape': 'diamond',
            'background-color': '#6785d0',
        });


// Cytoscape variable definition
var cy = cytoscape({
    style: stylesheet,
    layout: { name: 'preset' },
    container: document.getElementById('cyt'),
    ready: function() {}
});
