
(function ($, document, window) {

  $.extend($.fn, {
    Tooltip: function(msg, option) {
      var distance = 10;
      var time = 250;
      var hideDelay = 100;
      var hideDelayTimer = null;
      var beingShown = false;
      var shown = false;
      var canShow = false;
      var content,
          idbox = "tbox-" + $(this).attr('id'),
          idcontent = "tcontent-" + $(this).attr('id'),
          innerContent = '#tooltip-' + $(this).attr('id');

      content = '<div class="popup" id="'+ idbox +'">' +
          '<table id="dpop" cellpadding="0" border="0">' +
          '<tbody><tr>' +
          '<td id="topleft" class="corner"></td>' +
          '<td class="top"><img width="30" height="29" alt="" src="/static/images/bubble-tail2.png"/></td>' +
          '<td id="topright" class="corner"></td></tr><tr>' +
          '<td class="left"></td>' +
          '<td><div class="popup-contents" id="'+ idcontent +'"></div></td>' +
          '<td class="right"></td>' +
          '</tr><tr>' +
          '<td class="corner" id="bottomleft"></td>' +
          '<td class="bottom" valign="left"></td>' +
          '<td id="bottomright" class="corner"></td></tr>' +
          '</tbody></table>' +
          '</div>';
      $('body').append(content);
      var popupContent = $(innerContent).detach();
      popupContent.appendTo("#"+idcontent);
      $(idbox).css('opacity', 0);
      $(innerContent).show();

      function showUP($this) {
        if (!canShow){
          return false;
        }
        var height = $this.height();
        var top = $this.offset().top + height + 5;
        var left = $this.offset().left +($this.width()/2)-30;
        if (hideDelayTimer) clearTimeout(hideDelayTimer);
        if (beingShown || shown) {
          return;
        } else {
          // reset position of info box
          beingShown = true;
          $('#'+idbox).css({
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
      }

      function close(){
        if (hideDelayTimer) clearTimeout(hideDelayTimer);
        if (!shown) return false;
        hideDelayTimer = setTimeout(function () {
            hideDelayTimer = null;
            $('#'+idbox).animate({
                top: '-=' + distance + 'px',
                opacity: 0
            }, time, 'swing', function () {
                $('.popup').css('display', 'none');
                shown = false;
                canShow = false;
            });
        }, hideDelay);
      }

      $(this).click(function(){
        if (!canShow){
          canShow = true;
          showUP($(this));
        }
        else{
          close();
        }
        return false;
      });

      $("body").click(function(){
        close();
      });
      $('#'+idbox).click(function(e){
        e.stopPropagation();
      });
    }
  });

}(jQuery, document, this));