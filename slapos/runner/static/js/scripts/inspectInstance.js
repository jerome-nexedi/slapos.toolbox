$(document).ready( function() {
  var editor;
  setupFileTree();

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
});