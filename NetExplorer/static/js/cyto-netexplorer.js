$(document).ready(function(){
    // Cytoscape style definition
    var stylesheet = cytoscape.stylesheet()
        .selector('node')
            .css({
                'content': 'data(name)',
                'text-valign': 'center',
                'color': '#F8F8F8',
                'background-color': 'data(colorNODE)',
                'text-outline-width': 0.6,
                "font-size": 8,
                "text-outline-color": "#404040",
            })
        .selector('edge')
            .css({
                'content': 'data(probability)',
                'font-size': 6,
                'width': 1,
                'color': "#404040",
                'background-color': '#F8F8F8',
                'text-outline-width': 2,
                "text-outline-color": "#F8F8F8",
                'line-color': 'data(colorEDGE)',
                'target-arrow-color': 'data(colorEDGE)'
            });



    // Cytoscape variable definition
    var cy = cytoscape({
        style: stylesheet,
        layout: { name: 'preset' },
        container: document.getElementById('cyt'),
        ready: function() {}
    });


    if (upload_json) {
        cy.add(upload_json);
    }

    // CHANGE LAYOUT CONTROLS
    $('#select-layout li').on('click', function(){
        var newlayout = $(this).text().toLowerCase();
        cy.layout( { name: newlayout } )
    });

    $(".dropdown-menu li a").click(function(){
      $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
      $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
    });





    // Function used to add node

    function addNode(symbol, database) {
        $.ajax({
            type: "GET",
            url: "/net_explorer",
            cache: true,
            data: {
                'genesymbol': symbol,
                'database'  : database,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success : function(data) {
                var layout_name = $('#select-layout li').text().toLowerCase();
                var newelements = cy.add(data);

                cy.layout({
                    name: 'cola',
                    maxSimulationTime: 5000,
                    fit: true,
                    directed: false,
                    padding: 40
                });

                // Show only edges above slider threshold
                var value = $('#sl1').val();
                cy.filter(function(i, element){
                    if ( element.isEdge() ) {
                        if( element.data("probability") >= value ){
                            element.show();
                            return true;
                        }
                        element.hide()
                    }
                    // Not an edge
                });
            },
            error : function() {
                $('#node-not-found').slideToggle(200);
                setTimeout(function () {
                    $('#node-not-found').hide(200);
                }, 2000);
            }

        });
    }



    $("#add_node").submit(function(e) {
        var formObj = {};
        var dataArray = $("#add_node").serializeArray(),
        dataObj = {};
        $(dataArray).each(function(i, field){
            dataObj[field.name] = field.value;
        });
        addNode(dataObj['genesymbol'], dataObj['database']);
        e.preventDefault(); // avoid to execute the actual submit of the form.
    });


    // Info card/expand on click

    cy.on( 'click', 'node', function() {
         // Change color of clicked node
        node = this
        var card_data = {
            target  : this.data("name"),
            targetDB: this.data("database"),
            csrfmiddlewaretoken: '{{ csrf_token }}'
        }

        var behaviour = $('input[name=behaviour]:checked', '#behaviour-form').val()

        if (behaviour == "card") {
            // Get the ID of the div to update
            elementID = "card-overlay";
            $.ajax({
                type: "GET",
                url: "/info_card",
                data: {
                    'target'    : card_data['target'],
                    'targetDB'  : card_data['targetDB'],
                    'csrfmiddlewaretoken': '{{ csrf_token }}'
                },
                success : function(data) {
                    $('[id="' + elementID + '"]').html(data);
                    $('[id="card-overlay"]').slideToggle(450);
                    $('.close-overlay').slideToggle(450);
                    $('.full-screen-card').slideToggle(450);
                    $(document).ready(function(){
                        $('.int-table-class').DataTable({
                            "order": [[ 1, "desc" ]]
                        });
                    });
                }
            });
        } else if (behaviour == "expand") {
            node.data("colorNODE", '#449D44');
            addNode(card_data['target'], card_data['targetDB']);
        } else if (behaviour == "delete") {
            node.remove()
        }

    });



    // FILTER edges with probability below threshold
    $('#sl1').slider().on('slideStop', function(ev){
        //var value = $('#sl1').slider('getValue');
        var value = $('#sl1').val();
        cy.filter(function(i, element){
            if ( element.isEdge() ) {
                if( element.data("probability") >= value ){
                    element.show();
                    return true;
                }
                element.hide()
            }
            // Not an edge
        });


    });



    // CYTOSCAPE CONTROLS

    $(".btn").mouseup(function(){
        $(this).blur();
    })

    // Center graph
    $("#center-to-graph").on("click", function(){
        cy.center();
        cy.fit();
    });


    // Save png

    $("#image-download").on("click", function() {
        var graph_png = cy.png();
        $('#image-download').attr('href', graph_png);
    });


    // Export TBL
    $("#export-tbl").on("click", function(){
        alert("Export TBL")
    });


    // Save Graph
    $("#save-graph").on("click", function(){
        var jsonGraph = JSON.stringify(cy.json()['elements']);
        var blob = new Blob([jsonGraph], {type: "text/plain;charset=utf-8"});
        saveAs(blob, "graph-export.json");
    });


    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Delete All
    $("#delete-all").on("click", function() {
        cy.nodes().remove()
    });






    $('#node-not-found').hide();
});
