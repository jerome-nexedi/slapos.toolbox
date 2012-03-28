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
			$("#error").Popup("Please enter your file or folder name", {type:'alert', duration:3000});
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
					$("#error").Popup(data.result, {type:'error', duration:5000});
				}
				send = false;
			}
		});
		return false;
	});

	$("#save").click(function(){
		if(!edit){
			$("#error").Popup("Please select the file to edit", {type:'alert', duration:3000});
			return false;
		}
		if (send) return false;
		send = true;
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/saveFileContent',
			data: {file: $("input#subfolder").val(), content: editor.getSession().getValue()},
			success: function(data){
				if(data.code == 1){
					$("#error").Popup("File saved succefuly!", {type:'confirm', duration:3000});
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000});
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
	$("#getmd5").click(function(){
		getmd5sum();
		return false;
	});

	$("#clearselect").click(function(){
	    $("#info").empty();
	    $("#info").append("Select directory or nothing for root directory...");
	    $("input#subfolder").val("");
	    $("#edit_info").empty();
	    $("#edit_info").append("No file selected");
	    editor.getSession().setValue("");
	    $("#md5sum").empty();
	    $("a#option").hide();
	    return false;
	});
	$("#adddevelop").click(function(){
	    var developList = new Array();
	    var i=0;
	    $("#plist li").each(function(index){
		var elt = $(this).find("input:checkbox");
		if (elt.is(":checked")){
		    developList[i] = workdir+"/"+elt.val();
		    i++;
		    elt.attr("checked", false);
		}
	    });
	    if (developList.length > 0){setDevelop(developList);}
	    return false;
	});

	function getmd5sum(){
		var file = $("input#subfolder").val();
		if (send) return;
		send =true
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/getmd5sum',
			data: {file: $("input#subfolder").val()},
			success: function(data){
				if(data.code == 1){
					$("#md5sum").empty();
					$("#md5sum").append('md5sum : <span>' + data.result + '</span>');
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000});
				}
				send = false;
			}
		});
	}

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
	    $("#info").append("Select directory or nothing for root directory...");
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

	function selectFile(file){
		$("#info").empty();
		$("#info").append(file);
		$("input#subfolder").val(file);
		$("#md5sum").empty();
		path = "";
		send = false;
		edit = false;
		if(file.substr(-1) != "/"){
			$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/getFileContent',
			data: {file: file},
			success: function(data){
				if(data.code == 1){
					$("#edit_info").empty();
					var name = file.split('/');
					if(file.length > 65){
						//substring title.
						var start = file.length - 65;
						file = "..." + file.substring(file.indexOf("/", (start + 1)));
					}
					$("#edit_info").append("Current file: " +
						file);
					$("a#option").show();
					editor.getSession().setValue(data.result);
					setEditMode(name[name.length - 1]);
					edit = true;
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000});
				}
				send = false;
			}
		});
		}
		else{
			$("#edit_info").empty();
			$("#edit_info").append("No file selected");
			$("a#option").hide();
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
	function setDevelop(developList){
	    if (developList==null || developList.length <= 0) return;
	    editor.navigateFileStart();
	    editor.find('buildout',{caseSensitive: true,wholeWord: true});
	    if(!editor.getSelectionRange().isEmpty()){
		//editor.find("",{caseSensitive: true,wholeWord: true,regExp: true});
		//if(!editor.getSelectionRange().isEmpty()){
			//alert("found");
		//}
		//else{alert("no found");
		//}
	    }
	    else{
		$("#error").Popup("Can not found part [buildout]! Please make sure that you have a cfg file", {type:'alert', duration:3000});
		return;
	    }
	    editor.navigateLineEnd();
	    $.post($SCRIPT_ROOT+"/getPath", {file:developList.join("#")}, function(data) {
		    if(data.code==1){
			var result = data.result.split('#');
			editor.insert("\ndevelop =\n\t" + result[0] + "\n");
			for(var i=1; i<result.length; i++)
			    editor.insert("\t" + result[i] + "\n");
		    }
	    })
	    .error(function() {  })
	    .complete(function(){});
	    editor.insert("\n");
	}
});