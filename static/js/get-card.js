// GENE CARD WHEN CLICKING ON NODE OR IN SEARCHPANEL

function getCard(card_data) {
    // This function takes the data of a node stored in the
    // hash "card_data" and makes an AJAX request to info_card,
    // returning the data of the node and displaying a card div.
    elementID = "card-overlay";
    $.ajax({
        type: "GET",
        url: "/PlanNET/info_card",
        data: {
            'target'    : card_data.target,
            'targetDB'  : card_data.targetDB,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        success : function(data) {
            // Add history entry!
            history.pushState(card_data, null, "/PlanNET/gene_card/" + card_data.targetDB + "/" + card_data.target);

            // Get the HTML data
            $('[id="' + elementID + '"]').html(data);

            // Show the hidden div
            $('[id="card-overlay"]').slideToggle(450);
            $('.close-overlay').slideToggle(450);
            $('.full-screen-card').slideToggle(450);

            // Activate DataTable
            $('#int-table').DataTable({
                "order": [[ 1, "desc" ]]
            });

        }
    });
}


// Function that opens gene card when clicking on small-searchpanel

$(function() {
    $('.card-trigger').click(function() {
        var card_data = {
            target  : $(this).attr("target"),
            targetDB: $(this).attr("targetDB"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        };

        // Do AJAX request and load the html data
        getCard(card_data);
    });


});
