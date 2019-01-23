function changeLabels(cyobj) {
	var newLabel = $("#change-labels input:checked").val();
	if (newLabel == "human") {
		cyobj.nodes().addClass('human-label');
	} else {
		cyobj.nodes().removeClass('human-label');
	}
}