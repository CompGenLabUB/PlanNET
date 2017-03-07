// Count nodes
function countNodes(cyto) {
    var nodes = cyto.elements('node[database != "Human"]');
    var count = nodes.length;
    $("#node-count").html(count);
}
