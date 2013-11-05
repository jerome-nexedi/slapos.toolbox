/*jslint undef: true */
/*global $, window, document */
/* vim: set et sts=4: */

// jQuery Message Popup
// Display a message on the top of page, with floating
//

(function ($, document, window) {
  var isShow = null,
      top = 0,
      boxCount = 0,
      showDelayTimer = null;

  $.extend($.fn, {
    Popup: function(msg, option) {
      var h,
          $box = $(this),
          currentBox = 'bcontent' + boxCount;
      if (option.type === undefined) option.type = "info";
      if (option.closebtn === undefined) option.closebtn = false;
      if (option.duration === undefined) option.duration = 0;
      if (option.load === undefined) option.load = false;

      setupBox();

      function setupBox(){
        if (msg === undefined){
          msg = "Cannot execute your request. Please make sure you are logged in!!";
          option.type = "error";
        }
        $box.show();
        $box.css('top', + ($(window).scrollTop()) +'px');
        $box.append('<div id="' + currentBox + '" style="display:none" class="'+option.type+'"><table><tr>' +
        '<td valign="middle"><p>' + msg + '</p></td>' +
        '<td valign="top" class="b_close"><span id="pClose'+boxCount+'" class="pClose"></span></td></tr></table></div>');

        $("#pClose"+boxCount).bind("click", function() {
          close($("#"+currentBox));
        });
        $("#"+currentBox).fadeIn();
        boxCount++;
        $(window).scroll(function(){
          $box.animate({top:$(window).scrollTop()+"px" },{queue: false, duration: 350});
        });
        if(option.duration !== 0){
          showDelayTimer = setTimeout(function(){
            showDelayTimer = null;
            close($("#"+currentBox));
          }, option.duration);
        }
        if(option.load){
          $(window).load(function(){

          });
        }
      }
      function close($elt){
        $elt.unbind('click');
        $elt.fadeOut("slow", function() {
          $elt.remove();
        });
      }
    }
  });
}(jQuery, document, this));
