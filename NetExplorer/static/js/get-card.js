// GENE CARD WHEN CLICKING ON NODE OR IN SEARCHPANEL

function getCard(card_data) {
    // This function takes the data of a node stored in the
    // hash "card_data" and makes an AJAX request to info_card,
    // returning the data of the node and displaying a card div.
    elementID = "card-overlay";
    $.ajax({
        type: "GET",
        url: window.ROOT + "/info_card",
        data: {
            'target'    : card_data.target,
            'targetDB'  : card_data.targetDB,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        success : function(data) {
            // Add history entry!
            history.pushState(card_data, null, window.location.href);

            // Get the HTML data
            $('[id="' + elementID + '"]').html(data);

            // Show the hidden div
            $('[id="card-overlay"]').show(450);
            $('.close-overlay').show(450);
            $('.full-screen-card').show(450);

        }
    });
}


// Function that opens gene card when clicking on small-searchpanel

$(function() {
    $(document.body).on('click', '.card-trigger', function() {
        var card_data = {
            target  : $(this).attr("target"),
            targetDB: $(this).attr("targetDB"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        };

        // Do AJAX request and load the html data
        getCard(card_data);
    });

});
