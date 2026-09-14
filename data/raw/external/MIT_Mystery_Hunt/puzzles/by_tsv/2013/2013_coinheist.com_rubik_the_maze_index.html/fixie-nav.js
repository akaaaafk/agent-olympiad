$(document).ready(function(){

    var navExp = $('#fixie-nav-expanded');
    var hoverTimer;
    $('#fixie-nav').hover(
        function (e) {
            clearTimeout(hoverTimer);
            hoverTimer = undefined;
            navExp.filter(':hidden, :animated:not(.showing)').stop(true).addClass('showing').slideToggle('fast');
        },
        function (e) {
            clearTimeout(hoverTimer);
            hoverTimer = setTimeout(function() {
                navExp.filter(':visible:not(:animated), :visible.showing').stop(true).removeClass('showing').slideToggle('fast');
                hoverTimer = undefined;
            }, navExp.filter(':animated.showing').length ? 0 : 250);
        }
    );
});
