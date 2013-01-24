// jQuery Message Popup
// Display a message on the top of page, with floating
//

(function ($, document, window) {
  var isShow = null;
  var showDelayTimer = null;
  $.extend($.fn, {
    Popup: function(msg, option) {
      var h;
      if (option.type === undefined) option.type = "info";
      if (option.closebtn === undefined) option.closebtn = false;
      if (option.duration === undefined) option.duration = 0;
      if (option.load === undefined) option.load = false;
      var $box = $(this);
      if(showDelayTimer){clearTimeout(showDelayTimer);}
      if(isShow){
        $box.fadeOut('normal', function() {
          setupBox();
        });
      }
      else{setupBox();}
      function setupBox(){
        if (msg === undefined){
          msg = "Cannot execute your request. Please make sure you are logged in!!";
          option.type = "error";
        }
        $box.empty();
        $box.css('top','-1000px');
        $box.show();
        $box.append('<div><table id="bcontent"><tr>' +
        '<td valign="middle" class="logo ' + option.type + '_message"></td>' +
        '<td valign="middle"><p>' + msg + '</p></td>' +
        '<td valign="middle" class="b_close"><span id="pClose"></span></td></tr></table></div>');
        $(window).scroll(function(){
          $box.animate({top:$(window).scrollTop()+"px" },{queue: false, duration: 350});
        });
        h = $("#bcontent").height()+5;
        $("#pClose").bind("click", function() {
          close();
        });
        showBox();
        if(option.duration !== 0){
          showDelayTimer = setTimeout(function(){
            showDelayTimer = null;
            close();
          }, option.duration);
        }
      }
      function showBox(){
        if(option.load){
          $(window).load(function(){
            $box.css('top', + ($(window).scrollTop() - h) +'px');
            $box.animate({ top:"+=" + h + "px" }, "slow");
            isShow = true;
          });
        }
        else{
          $box.css('top', + ($(window).scrollTop() - h) +'px');
          $box.animate({ top:"+=" + h + "px" }, "slow");
          isShow = true;
        }
      }
      function close(){
        $box.animate({ top:"-=" + h + "px" }, "slow", function(){
          $box.fadeOut("normal", function() {
            isShow = false;
          });
        });
      }
    }
  });
}(jQuery, document, this));
