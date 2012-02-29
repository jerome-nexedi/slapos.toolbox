$(function () {
    var distance = 10;
    var time = 250;
    var hideDelay = 200;
    var hideDelayTimer = null;
    var beingShown = false;
    var shown = false;
    $('.popup').css('opacity', 0);
    $('a[rel=tooltip], .popup').mouseover(function () {
        var height = $(this).height();
        var top = $(this).offset().top + height + 5;
        var left = $(this).offset().left - ($(this).width() /2);
        if (hideDelayTimer) clearTimeout(hideDelayTimer);
        if (beingShown || shown) {
            return;
        } else {
            // reset position of info box
            beingShown = true;
            $('.popup').css({
                top: top,
                left: left,
                display: 'block'
            }).animate({
                top: '-=' + distance + 'px',
                opacity: 1
            }, time, 'swing', function() {
                beingShown = false;
                shown = true;
            });
        }
        return false;
    }).mouseout(function () {
        if (hideDelayTimer) clearTimeout(hideDelayTimer);
            hideDelayTimer = setTimeout(function () {
                hideDelayTimer = null;
                $('.popup').animate({
                    top: '-=' + distance + 'px',
                    opacity: 0
                }, time, 'swing', function () {
                    shown = false;
                    $('.popup').css('display', 'none');
                });
            }, hideDelay)
        return false;
    });
});