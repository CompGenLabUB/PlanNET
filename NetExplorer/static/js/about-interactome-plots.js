$(document).ready(function () {
    var divs = $('.plot-viewer>div');
    now = 0; // currently shown div
    divs.hide().first().show();
    $("div[name=next]").click(function (e) {
        divs.eq(now).hide();
        now = (now + 1 < divs.length) ? now + 1 : 0;
        var newtitle = divs.eq(now).attr("data-id");
        $(".plot-title").html(newtitle);
        divs.eq(now).show(); // show next
    });
    $("div[name=prev]").click(function (e) {
        divs.eq(now).hide();
        now = (now > 0) ? now - 1 : divs.length - 1;
        var newtitle = divs.eq(now).attr("data-id");
        $(".plot-title").html(newtitle);
        divs.eq(now).show(); // or .css('display','block');
        //console.log(divs.length, now);
    });
});


$(".view-interactome-plots").on("click", function(event){
    // Get back to first image when opening overlay
    var divs = $('.plot-viewer>div');
    now = 0;
    divs.hide().first().show();
    // Show the hidden div
    var transcriptome = $( this ).attr("data-id");
    var static_url    = $(".plot-viewer").attr("data-id") + transcriptome + "/";
    $( ".plot-img>img" ).each(function() {
        var img_name = $( this ).attr("data-id");
        var new_src  = static_url + img_name;
        $(this).attr("src", new_src);
    });
    $('.transcriptome-replace').html(transcriptome);
    $('.plot-title').html("Sequence Length");
    //$('[id="card-overlay"]').html("");

    // Show overlay
    $('[id="card-overlay"]').slideToggle(450);
    $('.close-overlay').slideToggle(450);

    // Prevent JS to close the overlay because some html element (the link) was clicked.
    event.stopPropagation();

});
