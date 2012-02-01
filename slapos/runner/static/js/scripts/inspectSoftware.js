$(document).ready( function() {
	var editor;
	var send = false;
	var runnerDir = $("input#runnerdir").val();
	var ajaxRun;
	fillContent();
	$("#softwarelist").change(function(){
		$("#info").empty();
		$("#info").append("Please select your file or folder into the box...");
		fillContent();
	});
	
	function selectFile(file){
		var relativeFile = file.replace(runnerDir + "/" + $("#softwarelist").val(), "");
		$("#info").empty();
		$("#info").append("Selection: " + relativeFile);
		return;
	}
	
	function fillContent(selectedElt){
		var folder = $("#softwarelist").val();
		var elt = $("option:selected", $("#softwarelist"));
		$('#fileTree').fileTree({ root: runnerDir + "/" + folder, script: $SCRIPT_ROOT + '/readFolder', 
			folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
			selectFile(file);
		}, function(file){ viewFile(file)});
		$("#softcontent").empty();		
		$("#softcontent").append("File content: " + elt.attr('title'));
	}
	
	$("#open").click(function(){
		var elt = $("option:selected", $("#softwarelist"));
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/setCurentProject',
			data: "path=" + elt.attr('rel'),
			success: function(data){
				if(data.code == 1){
					location.href = $SCRIPT_ROOT + '/editSoftwareProfile'
				}
				else{
					error(data.result);
				}
			}
		});
		return false;
	});
	
	$("#delete").click(function(){
		if(send) return;
		send = false;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/removeSoftwareDir',
			data: "name=" + $("#softwarelist").val(),
			success: function(data){
				if(data.code == 1){
					var folder = $("#softwarelist").val();
					$('#fileTree').fileTree({ root: runnerDir + "/" + folder, script: $SCRIPT_ROOT + '/readFolder', folderEvent: 'click', expandSpeed: 750,
						collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
					selectFile(file);
					setupFileTree(runnerDir);
					}, function(file){ viewFile(file)});
					$("input#file").val("");
					$("#flash").fadeOut('normal');
					$("#flash").empty();
					$("#info").empty();
					$("#info").append("Please select your file or folder into the box...");
					$("#softwarelist").empty();
					for(i=0; i<data.result.length; i++){
						$("#softwarelist").append('<option value="' + data.result[i]["md5"] + 
							'" title="' + data.result[i]["title"] +'" rel="' + 
							data.result[i]["path"] +'">' + data.result[i]["title"] + '</option>');
					}
				}
				else{
					error(data.result);
				}
				send = false;
			}
		});
		return false;	
	});
	
	function viewFile(file){
		//User have double click on file in to the fileTree
		var name = file.replace(runnerDir + "/" + $("#softwarelist").val(), "/software");
		loadFileContent(file, name);
	}
	
	function loadFileContent(file, filename){
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
					$("#flash").empty();
					$("#inline_content").empty();
					$("#inline_content").append('<h2 style="color: #4c6172; font: 18px \'Helvetica Neue\', Helvetica, Arial, sans-serif;">Inspect Software Content: ' +
						filename +'</h2>');
					$("#inline_content").append('<br/><div class="main_content"><pre id="editor"></pre></div>');
					setupEditor();
					$(".inline").colorbox({inline:true, width: "847px", onComplete:function(){						
						editor.getSession().setValue(data.result);
					}});
					$(".inline").click();
				}
				else{
					error("Error: Can not load your file, please make sure that you have selected a Software Release");
				}
			    }
			});
		      }
		      else{
			//Can not displays binary file
			error(data.result);
		      }
		    }
		    else{
		      error(data.result);
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
	
	function error(msg){
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');
		$("#flash").append("<ul class='flashes'><li>" + msg + "</li></ul>");
	}
});