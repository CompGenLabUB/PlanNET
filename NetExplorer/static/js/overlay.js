$('.card-overlay').hide();
$('.close-overlay').hide();


$('.small-searchpanel').click(function(){
    $('.card-overlay').hide(250);
    $('.close-overlay').hide();
    var card_data = {
        target  : $(this).attr("target"),
        targetDB: $(this).attr("targetDB"),
    }
    elementID = card_data["target"] + "_card";
    $("#" + elementID).slideToggle(450);
    $('.close-overlay').slideToggle(450);
    return false;
});

$('.close-overlay').click(function(){
    $('.card-overlay').hide(250);
    $('.close-overlay').hide();
});

$(document).keyup(function(e) {
    if(e.keyCode== 27) {
        $('.card-overlay').hide(250);
        $('.close-overlay').hide();

    }
});

$('html').click(function() {
    $('.card-overlay').hide(250);
    $('.close-overlay').hide();
 });

 $('.card-overlay').click(function(event){
     event.stopPropagation();
});

 $('.close-overlay').click(function(event){
     event.stopPropagation();
 });
