/* PlanExp */

var PlanExp = (function() {
    var expType = Object.freeze({"Single-Cell":1, "RNA-Seq":2});
    var currentExpType = false;


    /**
     * experimentSummary
     *   Summary:
     *     Performs AJAX query to /experiment_summary, 
     *     retrieving the HTML code of the summary and
     *     putting it on the targetDiv (as well as making it
     *     visible).
     *   Arguments:
     *     - Experiment name string
     *     - jQuery object of div to put the summary
     *     - jQuery object of DataSet Select to fill with available datasets
     *   Returns:
     *     - Nothing
     */
    experimentSummary = function(expName, targetDiv) {
        
        $.ajax({
            type: "GET",
            url: window.ROOT + "/experiment_summary",
            data: {
                'experiment'    : expName,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                // Change Exp type
                currentExpType = expType[data.exp_type];
                targetDiv.html(data.html);
                targetDiv.hide();
                targetDiv.show(250);
            },
            error: function(data) {
                console.log(data.responseText);
            }
        });
        
    }


    /**
     * fillConditions
     *   Summary:
     *     Performs AJAX query to /experiment_conditions,
     *     retrieving the conditions for a given experiment
     *     and filling all the Selects elements with those
     *     conditions.
     *   Arguments:
     *     - Experiment name string
     *     - jQuery object of select objects to fill.
     *   Returns:
     *     - Nothing
     */
    fillConditions = function(expName, conditionSelects) {

        conditionRow = function(conditionName, ctype) {
            return "<option class='condition-option " + 
                    ctype + "'" +
                    " value='" + 
                    conditionName + 
                    "'>" + 
                    conditionName + 
                    "</option>\n";
        }

        optGroupOpen = function(ctype) {
            console.log(

                "<optgroup label='" + 
                    ctype + 
                    "' " + 
                    "class='condition-option " + 
                    ctype + "'" +
                    ">\n"

            );
            return "<optgroup label='" + 
                    ctype + 
                    "' " + 
                    "class='condition-option " + 
                    ctype + "'" + 
                    ">\n";
        }

        optGroupClose = function() {
            return "</optgroup>\n";
        }

        $.ajax({
            type: "GET",
            url: window.ROOT + "/experiment_conditions",
            data: {
                'experiment'    : expName,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                conditionSelects.html(""); // clean previous HTML
                var keys = Object.keys(data);

                // Group conditions by Condition Type
                groups = {};
                for (var i=0; i<keys.length; ++i) {
                    if (! groups[ data[keys[i]] ]) {
                        groups[ data[keys[i]] ] = [];
                    }
                    groups[ data[keys[i]] ].push(keys[i]);
                }
                
                var html_to_add = "";
                // Add conditions to dropdowns sorted within each Condition Type.
                for (ctype in groups) {
                    html_to_add += optGroupOpen(ctype);
                    var conditions = groups[ctype];
                    conditions.sort();
                    for (cond in conditions) {
                        var conditionName = conditions[cond];
                        html_to_add += conditionRow(conditionName, ctype);
                    }
                    html_to_add += optGroupClose();
                    
                }
                conditionSelects.append(html_to_add);
                conditionSelects.selectpicker('refresh');
            },
            error: function(data) {
                console.log(data.responseText);
            }
        })
    }



    /**
     * fillCtypes
     *   Summary:
     *     Performs AJAX query to /experiment_condition_types,
     *     retrieving the condition types for a given experiment.
     *   Arguments:
     *     - Experiment name string
     *     - jQuery object of select objects to fill.
     *   Returns:
     *     - Nothing
     */
    fillCtypes = function(expName, ctypeSelects) {

        ctypeRow = function(conditionName) {
            return "<option class='condition-option' value='" + 
                    conditionName + 
                    "'>" + 
                    conditionName + 
                    "</option>";
        }

        $.ajax({
            type: "GET",
            url: window.ROOT + "/experiment_condition_types",
            data: {
                'experiment'    : expName,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                ctypeSelects.html(""); // clean previous HTML
                var first = true;
                for (const ctype in data) {
                    
                    ctypeName = data[ctype];
                    ctypeSelects.append(ctypeRow(ctypeName));
                    if (first) {
                        $('.condition-option[value=' + ctypeName + ']').attr('selected', 'selected');
                        first = false;
                    }
                }

                ctypeSelects.selectpicker('refresh');
            },
            error: function(data) {
                console.log(data.responseText);
            }
        })
    }

    /**
     * getDatasets
     *   Summary:
     *     
     *     
     *   Arguments:
     *    
     *   Returns:
     *    
     */
    getDatasets = function(expName, datasetSelect) {
        datasetRow = function(datasetName) {
            //<option data-content="<img class=" legend-db'="" src="/static/Images/legend-Adamidi.png">Adamidi' value='Adamidi'</option>


            //<option data-content="<img class='legend-db' src='{% static 'Images/' %}legend-{{ db.name }}.png'>{{ db.name }}" value="{{ db.name }}">{{ db.name }}</option>
            return "<option data-content='<img class=\"" +
                    "legend-db\" src=\"" +
                    window.ROOT + 
                    "/static/Images/legend-" + 
                    datasetName +
                    ".png\">" +
                    datasetName +
                    "'" +
                    " value='" +
                    datasetName +
                    "'" +
                    "</option>"; 
            //return "<option class='dataset-option' value='" + 
            //        datasetName + 
            //        "'>" + 
            //        datasetName + 
            //        "</option>";
        }

        $.ajax({
            type: "GET",
            url: window.ROOT + "/experiment_dataset",
            data: {
                'experiment': expName,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                datasetSelect.html("");
                for (const i in data) {
                    datasetName = data[i].fields.name;
                    datasetSelect.append(datasetRow(datasetName));
                }
                datasetSelect.selectpicker("refresh");
                datasetSelect.show(250);
            }
        });
    }


    /**
     * experimentDGETable
     *   Summary:
     *     Performs AJAX query to /experiment_dge_table, 
     *     retrieving the HTML code of the differential
     *     expression table and puting it in targetDiv.
     *   Arguments:
     *     - Experiment name string
     *     - jQuery object of div to put the table.
     *   Returns:
     *     - Nothing
     */
    experimentDGETable = function(expName, dataset, condition1, condition2, targetDiv) {
        condition1 = condition1.replace(/ \(.+\)/, "");
        condition2 = condition2.replace(/ \(.+\)/, "");

        $.ajax({
            type: "GET",
            url: window.ROOT + "/experiment_dge_table",
            data: {
                'experiment': expName,
                'dataset'   : dataset,
                'condition1': condition1,
                'condition2': condition2,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                if (jQuery.isEmptyObject(data)) {
                    targetDiv.hide();
                    $("#dge-table-notfound").show(250);
                } else {
                    $("#dge-table-notfound").hide();
                    targetDiv.html(data.table);
                    targetDiv.hide();
                    targetDiv.show(250);
                    Plotly.newPlot("volcano-plot", data.volcano);
                }
            }
        });
    }


    /**
     * plotGeneExpression
     *   Summary:
     *     Performs AJAX query to /plot_gene_expression, 
     *     retrieving the JSON data to pass to Plotly
     *   Arguments:
     *     - Experiment name
     *     - Dataset
     *     - Gene name
     *     - jQuery object of div to plot.
     *   Returns:
     *     - Nothing
     */
    plotGeneExpression = function(expName, dataset, geneName, ctype, plotDivId) {
        $("#expression-plot-loading").show();
        $("#" + plotDivId).html("");
        $.ajax({
            type: "GET",
            url: window.ROOT + "/plot_gene_expression",
            data: {
                'experiment': expName,
                'dataset'   : dataset,
                'gene_name' : geneName,
                'ctype'     : ctype,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                if (data) {
                    $("#plot-genenotfound").hide();
                    Plotly.newPlot(plotDivId, data.data, data.layout);
                } else {
                    $("#plot-genenotfound").show(250);
                }
                $("#expression-plot-loading").hide();
            }
        });
    }

    /**
     * plotTSNE
     *   Summary:
     *     Performs AJAX query to /plot_tsne to 
     *     retrieve the data for the TSNE plot to pass it 
     *     to Plotly.
     *   Arguments:
     *     - Experiment name
     *     - Dataset
     *     - Gene name
     *     - jQuery object of div to plot.
     *     - withcolor: Bool to indicate if color dimension is necessary (i.e.: if we are plotting a gene).
     *     - Type of condition.
     *     - Id of the plot.
     *   Returns:
     *     - Nothing
     */
    plotTSNE = function(expName, dataset, geneName, withcolor, ctype, plotDivId) {
        $("#tsne-plot-loading").show();
        $("#" + plotDivId).html("");
        $.ajax({
            type: "GET",
            url: window.ROOT + "/plot_tsne",
            data: {
                'experiment': expName,
                'dataset'   : dataset,
                'gene_name' : geneName,
                'ctype'     : ctype,
                'withcolor' : withcolor,
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                if (data) {
                    $("#plot-genenotfound").hide();
                    Plotly.newPlot(plotDivId, data.data, data.layout);
                } else {
                    $("#tsne-plot-genenotfound").show(250);
                }
                $("#tsne-plot-loading").hide();
            }
        });

    }


    showConditionTypes = function(selectDivClass, ctype) {
        $("." + selectDivClass + " option").prop("selected", false);
        $("." + selectDivClass + " option").hide();
        $("." + selectDivClass + " " + "." + ctype).show();

        $("." + selectDivClass).selectpicker("refresh");
    }


   /**
    * Add JSON Graph to Cytoscape
    **/
   addJsonToCy = function(graphelements) {
        try {
            window.cy = cytoscape({
                style: window.stylesheet,
                layout: { name: 'cola' },
                container: document.getElementById('planexp-cyt'),
                elements: graphelements,
                wheelSensitivity: 0.25,
                ready: function() {}
            })
            cy.layout({'name': 'cola'});
        }
        catch(err) {
            displayError("Incorrect graph definition");
        }
    }


    handleFileSelect = function(evt) {
        var files = evt.target.files; // FileList object
        // files is a FileList of File objects. List some properties.
        var output = [];
        var file = files[0];
        var format = "";
      
        // Read file
        var reader = new FileReader();
        reader.onload = function(){
          var graphelements;
          textfile = reader.result;
          // Check format
          if (evt.target.id == "import-json") {
            try {
              graphelements = JSON.parse(textfile);
              addJsonToCy(graphelements);
            }
            catch (err) {
              displayError("Incorrect JSON file.");
            }
          }

          // Close overlay
          $('.card-overlay-netcell-uploadgraph').slideToggle(450);
          $('.close-overlay-uploadgraph').slideToggle(450);
      
        };
        reader.readAsText(file);
    }


    /**
     * changeNetworkColor
     *   Summary:
     *     Changes the color gradient of the displayed network.
     *   Arguments:
     *     - Color gradient picked.
     *   Returns:
     *     - Nothing
     */
    changeNetworkColor = function(element) {
        $("#" + $(element).parent().attr("id") + " .color-pick").removeClass("active");
        $(element).addClass("active");
        var colorGradient = $(element).attr('id');
        console.log(colorGradient);
    }
      

    //----------------------------------------------------
    /* BUTTONS AND EVENTS */

    /**
     * selectExperiment
     *   Summary:
     *     Handles the selection of a given experiment.
     *     Performs all the actions necessary when that happens.
     */
    $("#select-experiment").on("change", function() { 
        var expName = $(this).val();
        experimentSummary(expName, $("#planexp-summary"));
        getDatasets(expName, $("#select-dataset"));
        fillConditions(expName, $("select.condition-select"));
        fillCtypes(expName, $("select.ctype-select"));

        // Hide and show on change 
        $("#planexp-summary-toc").show();
        $('#planexp-summary-toc').css('display', 'inline-block');
        $("#planexp-dge-table-container").hide();
        $("#planexp-dge-table-container-toc").hide();
        $("#planexp-gene-expression").hide();
        $("#planexp-gene-expression-toc").hide();
        $("#planexp-tsne").hide();
        $("#planexp-tsne-toc").hide();
        $("#planexp-network").hide();
        $("#planexp-network-toc").hide();
    });


    /**
     * Select Dataset
     *   Summary:
     *     Handles the selection of a given dataset.
     *     Will show the DGE table.
     */
    $("#select-dataset").on("change", function(){
        var dataset = $("#select-dataset").val();

        // Empty DGE table + Gene Plot and Deselect Conditions
        $("#planexp-dge-table").html("");
        $('#planexp-dge-c1').selectpicker('val', '');
        $('#planexp-dge-c2').selectpicker('val', '');
        $("#expression-plot").html("");
        $("#plot-tsne").html("");
        $("#volcano-plot").html("");
        $("#plot-genenotfound").hide();

        // Change DGE table ConditionType select
        var ctype = $("#planexp-dge-ctype").val();
        showConditionTypes("dge-table-condition-selects", ctype);

        // Change Network ConditionType select
        var ctype = $("#network-ctype").val();
        showConditionTypes("network-condition-selects", ctype);

        // Show the necessary cards
        $("#planexp-dge-table-container").show(250);
        $("#planexp-gene-expression").show(250);
        $("#planexp-dge-table-container-toc").show(250);
        $('#planexp-dge-table-container-toc').css('display', 'inline-block');
        $("#planexp-gene-expression-toc").show(250);
        $('#planexp-gene-expression-toc').css('display', 'inline-block');
        $("#planexp-network").show(250);
        $("#planexp-network-toc").show(250);
        if (currentExpType == expType['Single-Cell']) {
            $("#planexp-tsne").show(250);
            $("#planexp-tsne-toc").show(250);
            $('#planexp-tsne-toc').css('display', 'inline-block');
        }
    });



    /**
     * Select Condition for DGE table
     *   Summary:
     *     Handles the selection of the conditions for the.
     *     DGE table.
     */
    $("select.dge-table-condition-selects").on("change", function(){
        var expName = $("#select-experiment").val();
        var condition1 = $("#planexp-dge-c1").val();
        var condition2 = $("#planexp-dge-c2").val();
        var dataset = $("#select-dataset").val();
        if ( ! condition1 || ! condition2 ) {
            return;
        } 
        
        // Clean volcano plot 
        $("#volcano-plot").html("");
        experimentDGETable(expName, dataset, condition1, condition2, $("#planexp-dge-table"));

    });

    /**
     * Get Gene Expression Plot
     *   Summary:
     *     Plots gene expression 
     */
    $("#plot-expression-btn").on("click", function() {
        var expName  = $("#select-experiment").val();
        var dataset  = $("#select-dataset").val();
        var geneName = $("#gene-expression-search").val();
        var ctype    = $("#gene-expression-ctype").val();

        if (!geneName) {
            $("#plot-genenotfound").show(250);
            return;
        }
        $("#plot-genenotfound").hide();
        plotGeneExpression(expName, dataset, geneName, ctype, "expression-plot");
    })


    $("#planexp-dge-ctype").on("change", function(){
        var ctype = $("#planexp-dge-ctype").val();
        showConditionTypes("dge-table-condition-selects", ctype);
    });


    $("#plot-tsne-btn").on("click", function() {
        var expName  = $("#select-experiment").val();
        var dataset  = $("#select-dataset").val();
        var geneName = $("#tsne-search").val();
        var ctype    = $("#tsne-ctype").val();
        var activePanel = $("#planexp-tsne .tab-content .tab-pane.active");
        var withcolor = false;
        if (activePanel.attr('id') == "tsne-gene-tab") {
            withcolor = true;
            ctype = "Cluster";
            if (!geneName) {
                $("#tsne-plot-genenotfound").show(250);
                return;
            }
        }
        
        $("#tsne-plot-genenotfound").hide();
        plotTSNE(expName, dataset, geneName, withcolor, ctype, "tsne-plot");
    });


    // SCROLL BEHAVIOUR
    $(".planexp-toc-link").on("click", function(event){
        event.preventDefault();
        $.scrollTo($(this).attr("href"), 500);

    });

    // NETWORK CONDITIONS
    $("#network-ctype").on("change", function(){
        var ctype = $("#network-ctype").val();
        showConditionTypes("network-condition-selects", ctype);
    });

    // IMPORT NETWORK
    $(function(){
        document.querySelector("#import-json").addEventListener('change', handleFileSelect, false);
    });

    // NETWORK BUTTONS
    // CENTER
    $("#planexp-cyt-center").on("click", function() { cy.center(); cy.fit(); });

    

    // EXPORT
    $("#planexp-cyt-export").on("click", function() { 
        var jsonGraph = JSON.stringify(cy.json().elements);
        var blob = new Blob([jsonGraph], {type: "text/plain;charset=utf-8"});
        saveAs(blob, "graph-export.json"); 
    });

    // SAVE
    $("#planexp-cyt-save").on("click",   function() { var graph_png = cy.png(); $('#save-image-link').attr('href', graph_png); });
    
    // DELETE
    $("#planexp-cyt-delete").on("click", function() { 
        $( "#dialog-confirm" ).dialog({
            resizable: false,
            height: "auto",
            width: 400,
            modal: true,
            buttons: {
                Cancel: function() {
                    $( this ).dialog( "close" );
                },
                "Delete graph": function() {
                    cy.nodes().remove();
                    $( this ).dialog( "close" );
                }
            }
        })

     });

     // CHANGE LAYOUT
     $("#planexp-cyt-layout").on("change", function() {
        cy.layout({ name: $(this).val().toLowerCase() });
     });

    // NETWORK COLOR
    $(".color-pick").on("click", function() { changeNetworkColor(this) });

    // EDIT GRAPH DIALOG
     $("#close-edit-graph").on("click", function(){
        $("#edit-graph-dialog").hide(250);
     });

     // NETWORK



    // NETWORK EDITOR
    // -----------------------------------
    // EDIT
    $("#planexp-cyt-edit").on("click",   function() { 
        $("#edit-graph-dialog").show(250, function() {
            window.theEditor = new CyEditor('cytoscape-editor', cy);

            theEditor.cytoscape.edgehandles({
                toggleOffOnLeave: true,
                handleNodes: "node",
                handleSize: 10,
                handlePosition:'middle top', // sets the position of the handle in the format of "X-AXIS Y-AXIS" such as "left top", "middle top"
                edgeType: function() {
                    return 'flat';
                }
            });
        });
    });

    $("#editor-add-node-btn").on("click", function() {
        var nodeToAdd = $("#editor-add-node-text").val();
        var homologToAdd = $("#editor-add-node-homolog").val();
        theEditor.addNode(nodeToAdd, homologToAdd);
    });

    $(".editor-switch").on("change", function(){
        var currValue = $("input:checked", this).val();
        alert(currValue);
        if (currValue == "on") {
            // Change all other editor switches to OFF.
            var currInputOff = $("input[value=off]", this);
            $("input[value=off]", ".editor-switch").not(currInputOff).prop("checked", true);
        }
    });

    $("#editor-cancel").on("click", function(){
        $("#edit-graph-dialog").hide();
    })

    $("#editor-save").on("click", function(){
        if (theEditor.cytoscape.elements()) {
            cy.nodes().remove();
            cy.add( JSON.parse(JSON.stringify(theEditor.cytoscape.elements().jsons())));
            cy.layout({'name': 'cola'});
            $("#edit-graph-dialog").hide();
        }
    })



     
})();
