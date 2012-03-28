$(document).ready( function() {
  var editor;
  setupFileTree();
  $($("#slappart li")[0]).find("input:radio").attr('checked', true);
  $(".menu-box-right>div").css('min-height', $("#slappart li").length*26 + 20 + "px");
  configRadio();
  var lastli = null;
  var partitionAmount = $("imput#partitionAmount").val();
  $("#slappart li").each(function(){
    lastli = $(this);
    $(this).find("input:radio").change(function(){
  	  configRadio();      
	  });
  });  
  lastli.css("border-bottom", "none");    

  function setupFileTree(){
    var root = $("input#root").val();
    if (root == "") return;
    $('#fileTree').fileTree({ root: root, script: $SCRIPT_ROOT + "/readFolder", folderEvent: 'click', expandSpeed: 750,
      collapseSpeed: 750, multiFolder: false, selectFolder: false }, function(file) { 
		      
      }, function(file){
	//User have double click on file in to the fileTree
	viewFile(file);
    });
  }
  
  function viewFile(file){
	  //User have double click on file in to the fileTree
	  loadFileContent(file);
  }
  $("#parameter").load($SCRIPT_ROOT + '/getParameterXml');
  $("#update").click(function(){
    if($("#parameter").val() == ""){
        $("#error").Popup("Can not save empty value!", {type:'alert', duration:3000});
    }
    $.ajax({
        type: "POST",
    	url: $SCRIPT_ROOT + '/saveParameterXml',
    	data: {parameter: $("#parameter").val().trim()},
    	success: function(data){
            if(data.code == 1){
                $("#error").Popup("Instance parameters updated!", {type:'info', duration:3000});
            }
            else{
                $("#error").Popup(data.result, {type:'error', duration:5000});
            }
    	}
    });
  });
	
  function loadFileContent(file){
  $.ajax({
	type: "POST",
	url: $SCRIPT_ROOT + '/checkFileType',
	data: "path=" + file,
	success: function(data){
	  if(data.code == 1){
	    if (data.result=="text"){
	      $.ajax({
	      type: "POST",
	      url: $SCRIPT_ROOT + '/getFileContent',
	      data: {file:file, truncate:1500},
	      success: function(data){	
		      if(data.code == 1){
			$("#inline_content").empty();
			$("#inline_content").append('<h2 style="color: #4c6172; font: 18px \'Helvetica Neue\', Helvetica, Arial, sans-serif;">Inspect Instance Content: ' +
				file +'</h2>');
			$("#inline_content").append('<br/><div class="main_content"><pre id="editor"></pre></div>');
			setupEditor();
			$(".inline").colorbox({inline:true, width: "847px", onComplete:function(){						
				editor.getSession().setValue(data.result);
			}});
			$(".inline").click();
		      }
		      else{
			$("#error").Popup("Can not load your file, please make sure that you have selected a Software Release", {type:'alert', duration:5000});
		      }
		  }
	      });
	    }
	    else{
	      //Can not displays binary file
	      $("#error").Popup(data.result, {type:'alert', duration:5000});
	    }
	  }
	  else{
	    $("#error").Popup(data.result, {type:'alert', duration:5000});
	  }
	}
    });
  }
  function configRadio(){
  	$("#slappart li").each(function() {			
      var $radio = $(this).find("input:radio");
			var boxselector = "#box" + $radio.attr('id');      
			if($(this).hasClass('checked')){
				$(this).removeClass('checked');
				$(boxselector).slideUp("normal");
			}
			if($radio.is(':checked')){
				$(this).addClass('checked');
				//change content here
				$(boxselector).slideDown("normal");
        
			}
		});
	}
  function setupEditor(){		
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/crimson_editor");

    var CurentMode = require("ace/mode/text").Mode;
    editor.getSession().setMode(new CurentMode());
    editor.getSession().setTabSize(2);
    editor.getSession().setUseSoftTabs(true);
    editor.renderer.setHScrollBarAlwaysVisible(false);
    editor.setReadOnly(true);
  }
  function setupSlappart(){
    for(var i=0; i<partitionAmount; i++){
      var elt = $("#slappart"+i+"Parameter");
      if(elt != undefined) elt.click(function(){
        alert(elt.attr('id'));
      });        
    }
  }
});