$(document).ready( function() {
	var editor = ace.edit("editor");
	editor.setTheme("ace/theme/crimson_editor");

	var CurentMode = require("ace/mode/text").Mode;
	editor.getSession().setMode(new CurentMode());
	editor.getSession().setTabSize(2);
	editor.getSession().setUseSoftTabs(true);
	editor.renderer.setHScrollBarAlwaysVisible(false);
	    
	var script = "/readFolder";
	var softwareDisplay = true;
	var Mode = function(name, desc, clazz, extensions) {
		this.name = name;
		this.desc = desc;
		this.clazz = clazz;
		this.mode = new clazz();
		this.mode.name = name;
		
		this.extRe = new RegExp("^.*\\.(" + extensions.join("|") + ")$");
	};
	var modes = [		
		new Mode("php", "PHP",require("ace/mode/php").Mode, ["php", "in", "inc"]),
		new Mode("python", "Python", require("ace/mode/python").Mode, ["py"]),
		new Mode("buildout", "Python Buildout config", require("ace/mode/buildout").Mode, ["cfg"])
	    ];
	var projectDir = $("input#project").val();
	var workdir = $("input#workdir").val();
	var currentProject = workdir + "/" + projectDir.replace(workdir, "").split('/')[1];
	var send = false;
	var edit = false;	
	$('#fileTree').fileTree({ root: projectDir, script: $SCRIPT_ROOT + script, folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
		selectFile(file);
	});
	setDetailBox();
	$("#add").click(function(){
		var path = (softwareDisplay)? projectDir:currentProject;
		if (send) return false;
		if($("input#file").val() == "" || 
			$("input#file").val() == "Enter name here..."){
			error("Error: Please enter your file or folder name");
			return false;
		}
		if($("input#subfolder").val() != ""){
			path = $("input#subfolder").val();
		}
		path = path + "/" + $("input#file").val();
		send = true;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/createFile',
			data: "file=" + path + "&type=" + $("#type").val(),
			success: function(data){				
				if(data.code == 1){
					switchContent();
					$("input#file").val("");
					$("#flash").fadeOut('normal');
					$("#flash").empty();
					$("#info").empty();
					$("#info").append("Select parent directory or nothing for root...");
					$("input#subfolder").val("");					
				}
				else{
					error(data.result);
				}
				send = false;
			}
		});
		return false;
	});
	
	$("#save").click(function(){
		if(!edit){
			error("Please select the file to edit");
			return false;
		}
		send = false;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/saveFileContent',
			data: {file: $("input#subfolder").val(), content: editor.getSession().getValue()},
			success: function(data){				
				if(data.code == 1){
					$("#flash").fadeOut('normal');
					$("#flash").empty();
				}
				else{
					error(data.result);
				}
				send = false;
			}
		});
		return false;
	});
	
	$("#details_head").click(function(){
	    setDetailBox();
	});
	
	$("#switch").click(function(){
	    softwareDisplay = !softwareDisplay;
	    switchContent();
	    return false;
	});
	
	$("#clearselect").click(function(){
	    $("#info").empty();
	    $("#info").append("Select parent directory or nothing for root...");
	    $("input#subfolder").val("");
	    return false;
	});
	
	function switchContent(){
	    var root = projectDir;
	    if(!softwareDisplay){
		$("#switch").empty();
		$("#switch").append("Switch to Software files");
		root = currentProject;
	    }
	    else{
		$("#switch").empty();
		$("#switch").append("Switch to Project files");		
	    }
	    $('#fileTree').fileTree({ root: root, script: $SCRIPT_ROOT + script, folderEvent: 'click', expandSpeed: 750, collapseSpeed: 750, multiFolder: false, selectFolder: true }, function(file) { 
	        selectFile(file);
	    });
	    $("#info").empty();
	    $("#info").append("Select parent directory or nothing for root...");
	    $("input#subfolder").val("");
	}
	
	function setDetailBox(){
	    var state = $("#details_box").css("display");
	    if (state == "none"){
		$("#details_box").slideDown("normal");
		$("#details_head").removeClass("hide");
		$("#details_head").addClass("show");
	    }
	    else{
		$("#details_box").slideUp("normal");
		$("#details_head").removeClass("show");
		$("#details_head").addClass("hide");
	    }
	}
	
	function error(msg){
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');
		$("#flash").append("<ul class='flashes'><li>" + msg + "</li></ul>");
	}
	function selectFile(file){
		relativeFile = file.replace(workdir, "");
		$("#info").empty();
		$("#info").append(relativeFile);
		$("input#subfolder").val(file);
		path = "";
		send = false;
		edit = false;
		if(file.substr(-1) != "/"){			
			$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/getFileContent',
			data: "file=" + file,
			success: function(data){				
				if(data.code == 1){
					$("#flash").fadeOut('normal');
					$("#flash").empty();
					$("#edit_info").empty();
					var name = file.split('/');
					$("#edit_info").append("Edit selected file: " +
						relativeFile);
					editor.getSession().setValue(data.result);
					setEditMode(name[name.length - 1]);
					edit = true;
				}
				else{
					error(data.result);
				}
				send = false;
			}
		});
		}
		else{
			$("#edit_info").empty();
			$("#edit_info").append("Edit your selected file");
			editor.getSession().setValue("");
		}
		return;
	}
	
	function setEditMode(file){
		var CurentMode = require("ace/mode/text").Mode;		
		editor.getSession().setMode(new CurentMode());
		for (var i=0; i< modes.length; i++){
			if(modes[i].extRe.test(file)){
				editor.getSession().setMode(modes[i].mode);
				set = true;
				break;
			}
		}
	}
});