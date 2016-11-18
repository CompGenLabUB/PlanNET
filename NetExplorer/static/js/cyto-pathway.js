
// Cytoscape style definition
var stylesheet = cytoscape.stylesheet()
    .selector('node')
        .css({
            'content': 'data(name)',
            'text-valign': 'center',
            'color': '#F8F8F8',
            'background-color': 'data(colorNODE)',
            'text-outline-width': 0.6,
            "font-size": 8,
            "text-outline-color": "#404040",
        })
    .selector('edge')
        .css({
            'content': 'data(probability)',
            'font-size': 6,
            'width': 1,
            'color': "#404040",
            'background-color': '#F8F8F8',
            'text-outline-width': 2,
            "text-outline-color": "#F8F8F8",
            'line-color': 'data(colorEDGE)',
            'target-arrow-color': 'data(colorEDGE)'
        })
    .selector('edge[type = "homology"]')
        .css({
            'line-style': 'dashed',
            'content': '',
            'opacity': 0.8
        })
    .selector('node[database = "Human"]')
        .css({
            'shape': 'diamond',
        });
