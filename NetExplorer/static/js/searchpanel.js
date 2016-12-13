// Function that opens gene card when clicking on small-searchpanel

$(function() {
    $('.small-searchpanel').click(function() {
        var card_data = {
            target  : $(this).attr("target"),
            targetDB: $(this).attr("targetDB"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        };

        // Add history entry!!
        history.pushState(card_data, null, "/gene_card/" + card_data.targetDB + "/" + card_data.target);

        // Get the ID of the div to update
        getCard(card_data);
    });


});
