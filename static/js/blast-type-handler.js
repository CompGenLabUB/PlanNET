
$('#database-selection').change(function () {
    var selectedText = $(this).find("option:selected").text();
    if (selectedText === "Human") {
        // Human, protein database
        $('#blastn').attr("disabled", "disabled");
        $('#tblastn').attr("disabled", "disabled");
        $('#tblastx').attr("disabled", "disabled");
        $('#blastx').removeAttr("disabled");
        $('#blastp').removeAttr("disabled");
        $('.selectpicker').selectpicker('refresh');
    } else {
        // Planaria, nucleotide database
        $('#blastp').attr("disabled", "disabled");
        $('#blastx').attr("disabled", "disabled");
        $('#tblastx').removeAttr("disabled");
        $('#blastn').removeAttr("disabled");
        $('#tblastn').removeAttr("disabled");
        $('.selectpicker').selectpicker('refresh');
    }
});
