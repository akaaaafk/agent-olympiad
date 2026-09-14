var ellipsis = ['', '.', '..', '...'];

function animateEllipsis(el, count) {
    $(el).html(ellipsis[count%4]);
    if(true) {
        window.setTimeout( function(){
            animateEllipsis(el, ++count);
        }, 350);
    }
}

$(document).ready(function() {
    animateEllipsis($('.ellipsis-span'), 0);
});
