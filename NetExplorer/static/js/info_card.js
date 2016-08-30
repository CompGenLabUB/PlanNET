$(function() {
    $('.small-searchpanel').click(function() {
        var card_data = {
            symbol  : $(this).attr("data-symbol"),
            database: $(this).attr("data-database"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        }
        elementID = card_data["symbol"] + "_card";
        $("#" + elementID).load("{% url get_card %}?symbol=" + card_data["symbol"] + "&database=" + card_data["database"]);
        //$(this).nextAll(".card-overlay").load("/");
        //$(this).closest('.card-overlay').load("/");
    });
});
