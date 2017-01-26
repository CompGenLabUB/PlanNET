// Cytoscape style definition for pathway finder
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
    .selector('node[database = "Human"]')
        .css({
            'shape': 'diamond',
        });
