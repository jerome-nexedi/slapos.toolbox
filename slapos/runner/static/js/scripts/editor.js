$(document).ready( function() {
	var editor = ace.edit("editor");
	editor.setTheme("ace/theme/crimson_editor");

	var CurentMode = require("ace/mode/buildout").Mode;
	editor.getSession().setMode(new CurentMode());
	editor.getSession().setTabSize(2);
	editor.getSession().setUseSoftTabs(true);
	editor.renderer.setHScrollBarAlwaysVisible(false);
	    	
	var file = $("input#profile").val();
	var edit = false;
	selectFile(file);
	
	$("#save").click(function(){
		if(!edit){
			$("#error").Popup("Can not load your file, please make sure that you have selected a Software Release", {type:'alert', duration:5000});
			return false;
		}
		send = false;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/saveFileContent',
			data: {file: file, content: editor.getSession().getValue()},
			success: function(data){				
				if(data.code == 1){
					$("#error").Popup("File Saved!", {type:'confirm', duration:2000});
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000});
				}
				send = false;
			}
		});
		return false;
	});
	
	function selectFile(file){
		edit = false;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/getFileContent',
			data: "file=" + file,
			success: function(data){	
				if(data.code == 1){
					editor.getSession().setValue(data.result);
					edit = true;
				}
				else{
					$("#error").Popup("Can not load your file, please make sure that you have selected a Software Release", {type:'alert', duration:5000});
				}
			}
		});
		return;
	}
});