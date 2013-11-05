$(document).ready(function(){
  $(".tabContents").hide(); // Hide all tab content divs by default
  var hashes = window.location.href.split('#');
  var fromheight = 0;
  var previoustab = null;
  if (hashes.length == 2 && hashes[1] !== ''){
    $("#tabContainer>ul li").each(function() {
      var $tab = $(this).find("a");
      if($tab.hasClass("active")){
        $tab.removeClass("active");
      }
      if ($tab.attr("href") == "#"+hashes[1]){
        $tab.addClass("active");
        $("#"+hashes[1]).show();
        previoustab = "#"+hashes[1];
      }
      //alert($(this).attr("href"));
    });
  }
  else{$(".tabContents:first").show(); previoustab = ".tabContents:first";} // Show the first div of tab content by default
  $("#tabContainer ul li a").click(function(){ //Fire the click event
    if($(this).hasClass('active')){
        return false;
    }
    fromheight = $(previoustab).height();
    var activeTab = $(this).attr("href"); // Catch the click link
    $("#tabContainer .tabDetails").css("height", $("#tabContainer .tabDetails").height());
    $("#tabContainer ul li a").removeClass("active"); // Remove pre-highlighted link
    $(this).addClass("active"); // set clicked link to highlight state
    $(".tabContents").hide(); // hide currently visible tab content div
    $(activeTab).fadeIn(); // show the target tab content div by matching clicked link.
    var diff = fromheight - $(activeTab).height();
    if (diff > 0){$("#tabContainer .tabDetails").animate({height: '-=' + diff + 'px'}, 850, 'swing', function() {
      $("#tabContainer .tabDetails").css("height", "");
    });}
    else{diff = -1*diff; $("#tabContainer .tabDetails").animate({height: '+=' + diff + 'px'}, 850, 'swing', function() {
      $("#tabContainer .tabDetails").css("height", "");
    });}
    previoustab = activeTab;
    $("#tabContainer .tabDetails").css("height", $("#tabContainer .tabDetails").height());
    return false;//this reinitialize tab index when reload page
  });
});