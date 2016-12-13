// Function that opens gene card when clicking on small-searchpanel

$(function() {
    $('.small-searchpanel').click(function() {
        var card_data = {
            target  : $(this).attr("target"),
            targetDB: $(this).attr("targetDB"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        };

        // Do AJAX request and load the html data
        getCard(card_data);
    });


});
