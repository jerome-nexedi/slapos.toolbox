$(function () {
    var distance = 10;
    var time = 250;
    var hideDelay = 200;
    var hideDelayTimer = null;
    var beingShown = false;
    var shown = false;
    var canShow = false;
    $('.popup').css('opacity', 0);
    $('a[rel=tooltip], span[rel=tooltip]').click(function(){
      if (!canShow){
        canShow = true;
        $(this).mouseover();
      }
      else{
        $(this).mouseout();
      }
      return false;
    });
    $('a[rel=tooltip], span[rel=tooltip], .popup').mouseover(function () {
      if (!canShow){
        return false;
      }
      var height = $(this).height();
      var top = $(this).offset().top + height;
      var left = $(this).offset().left +($(this).width()/2)-30;
      var content = "#tooltip-" + $(this).attr('id');
      if (hideDelayTimer) clearTimeout(hideDelayTimer);
      if (beingShown || shown) {
        return;
      } else {
        $('#jqtooltip').empty();
        var contentValue = $(content).clone(true, true);
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
    });
    $('a[rel=tooltip], span[rel=tooltip], .popup').mouseout(function () {
      if (hideDelayTimer) clearTimeout(hideDelayTimer);
      hideDelayTimer = setTimeout(function () {
          hideDelayTimer = null;
          $('.popup').animate({
              top: '-=' + distance + 'px',
              opacity: 0
          }, time, 'swing', function () {
              $('.popup').css('display', 'none');
              shown = false;
              canShow = false;
          });
      }, hideDelay);
      return false;
    });
});