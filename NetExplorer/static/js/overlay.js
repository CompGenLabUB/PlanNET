$('.card-overlay').hide();

$('.small-searchpanel').click(function(){
    $('.card-overlay').hide(250);
    $(this).next().slideToggle(450);
    return false;
});

$('.close-overlay').click(function(){
    $('.card-overlay').hide(250);
    alert("MEEC");
});

$(document).keyup(function(e) {
    if(e.keyCode== 27) {
        $('.card-overlay').hide(250);

    }
});

$('html').click(function() {
 //your stuf
    $('.card-overlay').hide(250);
 });

 $('.card-overlay').click(function(event){
     event.stopPropagation();
});
