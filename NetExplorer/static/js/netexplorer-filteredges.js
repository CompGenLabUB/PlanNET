
// --------------------------
// FILTER EDGES BY CONFIDENCE
function filterByConfidence(confvalue, cyobj, plenval) {
    var to_show_selector = "";
    var to_hide_selector = "";
    if (plenval == "hide") {
        to_show_selector = "edge[pathlength=1][probability>=" + confvalue + "]";
        to_hide_selector = "edge[probability<" + confvalue + "]";
    } else {
        to_show_selector = "edge[probability>=" + confvalue + "]";
        to_hide_selector = "edge[probability<" + confvalue + "]";
    }
    // Take into account if check Plen is toggled
    // Filter
    cyobj.elements(to_show_selector).show();
    cyobj.elements(to_hide_selector).hide();
}


// --------------------------
// FILTER EDGES BY Plen
function checkPlen(value, cyobj, confvalue) {
    if (value == "show") {
        var show_selector = "edge" + "[probability>=" + confvalue + "]";
        cyobj.elements(show_selector).show();
    } else {
        cyobj.elements("edge[pathlength=2]").hide();
    }
}
