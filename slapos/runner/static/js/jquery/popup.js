// jQuery Message Popup
// Display a message on the top of page, with floating
//

(function ($, document, window) {
  $.extend($.fn, {
    Popup: function(msg, option) {
      if (option.type == undefined) option.type = "info";
      if (option.closebtn == undefined) option.closebtn = false;
      if (option.duration == undefined) option.duration = 0;
      if (option.load == undefined) option.load = false;
      $box = $(this);  
      $box.empty();
      $box.css('top','-1000px');
      $box.show();
      $box.append('<div><table id="bcontent"><tr>' +
	    '<td valign="middle" class="logo ' + option.type + '_message"></td>' +
	    '<td valign="middle"><p>' + msg + '</p></td>' +
	    '<td valign="middle" class="close"><span id="pClose"></span></td></tr></table></div>');         
      $(window).scroll(function(){
	$box.animate({top:$(window).scrollTop()+"px" },{queue: false, duration: 350});
      });
      var h = $("#bcontent").height()+5;
      $("#pClose").bind("click", function() {
	close();
      });
      if(option.load){
	$(window).load(function(){
	  $box.css('top', + ($(window).scrollTop() - h) +'px');
	  $box.animate({ top:"+=" + h + "px" }, "slow");
	});
      }
      else{
	$box.css('top', + ($(window).scrollTop() - h) +'px');
	$box.animate({ top:"+=" + h + "px" }, "slow");
      }
      if(option.duration != 0){
	setTimeout(function(){
	  close();
	}, option.duration);
      }
      function close(){
	$box.animate({ top:"-=" + h + "px" }, "slow", function(){
	  $box.fadeOut("normal");
	});
      }
    }
  });  
}(jQuery, document, this));