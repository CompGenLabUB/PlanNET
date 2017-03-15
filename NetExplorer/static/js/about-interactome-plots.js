$(document).ready(function () {
    var alldivs = $('.plot-viewer>div');
    var divs    = {};
    alldivs.each(function(){
        var transcriptome = $( this ).attr("data-id");
        if (! divs[transcriptome]) {
            $( this ).show();
            divs[transcriptome] = [];
        } else {
            $( this ).hide();
        }
        divs[transcriptome].push(this);
    });
    var now = {};
    $('.plot-viewer').each(function(){
        now[ $( this ).attr("data-id") ] = 0;
    });

    $("div[name=next]").click(function (e) {
        var transcriptome = $( this ).attr("data-id");
        $( divs[transcriptome] ).eq(now[transcriptome]).hide();
        now[transcriptome] = (now[transcriptome] + 1 < divs[transcriptome].length) ? now[transcriptome] + 1 : 0;
        var newtitle = $( divs[transcriptome] ).eq(now[transcriptome]).attr("data-id");
        //$(".plot-title").html(newtitle);
        $( divs[transcriptome] ).eq(now[transcriptome]).show(); // show next
    });
    $("div[name=prev]").click(function (e) {
        var transcriptome = $( this ).attr("data-id");
        $( divs[transcriptome] ).eq(now[transcriptome]).hide();
        now[transcriptome] = (now[transcriptome] > 0) ? now[transcriptome] - 1 : divs[ transcriptome ].length - 1;
        var newtitle = $( divs[transcriptome] ).eq(now[transcriptome]).attr("data-id");
        //$(".plot-title").html(newtitle);
        $( divs[transcriptome] ).eq(now[transcriptome]).show(); // or .css('display','block');
        //console.log(divs.length, now);
    });
});



$(".plot-bigger").on("click", function(event){
    var transcriptome = $(this).attr("data-id");
    var selector = "." + transcriptome + ".plot-img-png:visible";
    var new_src  = $(selector).attr("src");
    $(".img-bigger").attr("src", new_src);
    $('.card-overlay').slideToggle(450);
    $('.close-overlay').slideToggle(450);
    event.stopPropagation();
});
