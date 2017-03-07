// This script contains the general behaviour of card overlay divs

$('.card-overlay').hide();
$('.close-overlay').hide();
$('.full-screen-card').hide();

$('.close-overlay').click(function(){
    $('.card-overlay').hide(250);
    $('.close-overlay').hide();
    $('.full-screen-card').hide();
});

$(document).keyup(function(e) {
    if(e.keyCode== 27) {
        $('.card-overlay').hide(250);
        $('.close-overlay').hide();
        $('.full-screen-card').hide();

    }
});


$('html').click(function() {
    $('.card-overlay').hide(250);
    $('.close-overlay').hide();
    $('.full-screen-card').hide();
 });

 $('.card-overlay').click(function(event){
     event.stopPropagation();
});

 $('.close-overlay').click(function(event){
     event.stopPropagation();
 });


 $('.full-screen-card').click(function(event){
    event.stopPropagation();
    window.open(window.location.href);
 });
