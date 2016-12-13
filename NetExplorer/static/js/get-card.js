// GENE CARD WHEN CLICKING ON NODE OR IN SEARCHPANEL

function getCard(card_data) {
    // This function takes the data of a node stored in the
    // hash "card_data" and makes an AJAX request to info_card,
    // returning the data of the node and displaying a card div.
    elementID = "card-overlay";
    $.ajax({
        type: "GET",
        url: "/info_card",
        data: {
            'target'    : card_data.target,
            'targetDB'  : card_data.targetDB,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        success : function(data) {
            $('[id="' + elementID + '"]').html(data);
            $('[id="card-overlay"]').slideToggle(450);
            $('.close-overlay').slideToggle(450);
            $('.full-screen-card').slideToggle(450);

        }
    });
}
