$(document).ready( function() {
  openedlogpage = $("input#type").val();
  updatelogBox();
  var state = getCookie("autoUpdate");

  $("#logheader").click(function(){
    setupBox();
  });
  $("#manual").change(function(){
    setCookie("autoUpdate", "manual");
    if ($("input#type").val() == "instance"){location.href = $SCRIPT_ROOT + "/viewInstanceLog";}
    else{location.href = $SCRIPT_ROOT + "/viewSoftwareLog";}
  });
  $("#live").change(function(){
    updatelogBox();$("#logconfigbox").find("input:radio").attr('checked', false);$("#live").attr('checked', true);
    setSpeed(100);setCookie("autoUpdate", "live");openedlogpage = $("input#type").val();});
  $("#slow").change(function(){
    updatelogBox();$("#logconfigbox").find("input:radio").attr('checked', false);$("#slow").attr('checked', true);
    setSpeed(2500);setCookie("autoUpdate", "slow");openedlogpage = $("input#type").val();});
  if(state){
    $("#"+state).attr('checked', true);
    updatelogBox();
    if (state == "manual"){
      openedlogpage = ""; setSpeed(0);
    }
    else{setSpeed((state=="live")?100:2500);}
  }
  else{$("#slow").attr('checked', true);}

  function setupBox(){
    var state = $("#logconfigbox").css("display");
    if (state == "none"){
      $("#logconfigbox").slideDown("normal");
      $("#logheader").removeClass("hide");
      $("#logheader").addClass("show");
    }
    else{
      $("#logconfigbox").slideUp("normal");
      $("#logheader").removeClass("show");
      $("#logheader").addClass("hide");
    }
  }

  function updatelogBox(){
    if(processState=="Stopped" || processState=="Checking" || $("#manual").is(":checked")){
      $("#salpgridLog").hide();
      $("#manualLog").show();
      $("#manualLog")
        .scrollTop($("#manualLog")[0].scrollHeight - $("#manualLog")
          .height());
    }
    else{
      $("#salpgridLog").show();
      $("#manualLog").hide();
    }
  }
});