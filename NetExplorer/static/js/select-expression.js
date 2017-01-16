$("#select-expression").on("change", function(){
    alert($("#select-expression").val());

    var elements = get_graphelements(cy);

    $.ajax({
        type: "GET",
        url: "/map_expression",
        cache: true,
        data: {
            'file': $("#select-expression").val(),
            'nodes': elements.node_ids,
            'databases': elements.databases,
            'csrfmiddlewaretoken': '{{ csrf_token }}'
        },
        beforeSend: function() {
            $('#loading').show();
        },
        success : function(data) {
            $('#loading').hide();
        },
        error : function(err) {
            $('#loading').hide();
        }
    });
});
