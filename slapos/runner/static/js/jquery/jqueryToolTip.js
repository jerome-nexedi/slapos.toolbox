$(function () {
    var distance = 10;
    var time = 250;
    var hideDelay = 200;
    var hideDelayTimer = null;
    var beingShown = false;
    var shown = false;
    $('.popup').css('opacity', 0);
    $('a[rel=tooltip], a[rel=tooltip-min], .popup').mouseover(function () {
        var height = $(this).height();
        var top = $(this).offset().top + height;
        var left = $(this).offset().left - ($(this).width() /2);
        var content = "#tooltip-" + $(this).attr('id');
        if (hideDelayTimer) clearTimeout(hideDelayTimer);
        if (beingShown || shown) {
            return;
        } else {                  
            $('#jqtooltip').empty();
            var contentValue = $(content).clone(true, true);
            /*$(contentValue).find("*").each(function(index, element) {
              if(element.id){element.id = "jqt_" + element.id;}
               if($(this).attr('for')){$(this).attr('for', 'jqt_' + $(this).attr('for'))}
               //var events = $(content).get[0];
               //for (var type in events)
  		          // for (var handler in events[type])
				          // jQuery.event.add(this, type, events[type][handler], events[type][handler].data);
            });*/
            $(contentValue).appendTo('#jqtooltip');
            $('#jqtooltip ' + content).show();
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
                    $('.popup').css('display', 'none');
                    shown = false;
                });
            }, hideDelay)
        return false;
    });
});