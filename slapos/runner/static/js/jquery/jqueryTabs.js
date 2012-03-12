$(document).ready(function(){
	$(".tabContents").hide(); // Hide all tab content divs by default	
  var hashes = window.location.href.split('#');  
  if (hashes.length == 2){
    $("#tabContaier>ul li").each(function() {
      var $tab = $(this).find("a");
      if($tab.hasClass("active")) $tab.removeClass("active");
      if ($tab.attr("href") == "#"+hashes[1]){
        $tab.addClass("active");
        $("#"+hashes[1]).show();
      }
      //alert($(this).attr("href"));
    });
  }
  else{$(".tabContents:first").show();} // Show the first div of tab content by default
	$("#tabContaier ul li a").click(function(){ //Fire the click event
		if($(this).hasClass('active')){
		    return;
		}
		var activeTab = $(this).attr("href"); // Catch the click link
		$("#tabContaier ul li a").removeClass("active"); // Remove pre-highlighted link
		$(this).addClass("active"); // set clicked link to highlight state
		$(".tabContents").hide(); // hide currently visible tab content div
		$(activeTab).fadeIn(); // show the target tab content div by matching clicked link.
	});
});