$(document).ready( function() {
	var send = false;
	var getStatus;
	gitStatus();
	$("#project").change(function(){
		if (send){
			getStatus.abort();
			send=false;
		}
		gitStatus();
	});
	$("#activebranch").change(function(){
		var branch = $("#activebranch").val();
		var project = $("#project").val();
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/changeBranch',
			data: "project=" + $("input#workdir").val() + "/" + project + "&name=" + branch,
			success: function(data){
				if(data.code == 1){
					gitStatus();
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000});
				}
			}
		});
	});
	$("#addbranch").click(function(){
		checkout("1");
		return false;
	});
	$("#docheckout").click(function(){
		checkout("0");
		return false;
	});
	$("#commit").click(function(){
		if($("input#commitmsg").val() == "" ||
			$("input#commitmsg").val() == "Enter message..."){
			$("#error").Popup("Please Enter the commit message", {type:'alert', duration:3000});
			return false;
		}
		if (send){
			return false;
		}
		send = true;
		var project = $("#project").val();
		$("#imgwaitting").fadeIn('normal');
		$("#commit").empty();
		$("#commit").attr("value", "Wait...");
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/pushProjectFiles',
			data: {project: $("input#workdir").val() + "/" + project, msg: $("input#commitmsg").val()},
			success: function(data){
				if(data.code == 1){
					if (data.result != ""){
						$("#error").Popup(data.result, {type:'error', duration:5000});
					}
					else
						$("#error").Popup("Commit done!", {type:'confirm', duration:3000});
					gitStatus();
				}
				else{
					$("#error").Popup(data.result, {type:'error'});
				}
				$("#imgwaitting").hide()
				$("#commit").empty();
				$("#commit").attr("value", "Commit");
				send = false;
			}
		});
		return false;
	});
	/*
	$("#pullbranch").click(function(){
		if (send){
			return false;
		}
		send = true;
		var project = $("#project").val();
		$("#pullimgwaitting").fadeIn('normal');
		$("#pullbranch").empty();
		$("#pullbranch").attr("value", "Wait...");
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/pullProjectFiles',
			data: "project=" + $("input#workdir").val() + "/" + project,
			success: function(data){
				if(data.code == 1){
					if (data.result != ""){
						error(data.result);
					}
					else
						error("Pull done!");
					gitStatus();
				}
				else{
					error(data.result);
				}
				$("#pullimgwaitting").hide()
				$("#pullbranch").empty();
				$("#pullbranch").attr("value", "Git Pull");
				send = false;
			}
		});
		return false;
	});*/
	function gitStatus(){
		var project = $("#project").val();
		$("#status").empty();
		$("#push").hide();
		$("#flash").empty();
		if (project == ""){
			$("#status").append("<h2>Please select one project...</h2><br/><br/>");
			$("#branchlist").hide();
			return;
		}
		send = true;
		var urldata = $("input#workdir").val() + "/" + project;
		getStatus = $.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/getProjectStatus',
			data: "project=" + urldata,
			success: function(data){
				if(data.code == 1){
					$("#branchlist").show();
					$("#status").append("<h2>Your Repository status</h2>");
					message = data.result.split('\n').join('<br/>');
					//alert(message);
					$("#status").append("<p>" + message + "</p>");
					if(data.dirty){
						$("#push").show();
						$("#status").append("<br/><h2>Display Diff for current Project</h2>");
						$("#status").append("<p style='font-size:15px;'>You have changes in your project." +
							" <a href='" + $SCRIPT_ROOT + "/getProjectDiff/"
							+ encodeURI(project) + "'>Watch the diff</a></p>");
					}
					loadBranch(data.branch);
				}
				else{
					$("#error").Popup(data.result, {type:'error', duration:5000});
				}
				send = false;
			}
		});
	}
	function checkout(mode){
		if($("input#branchname").val() == "" ||
			$("input#branchname").val() == "Enter the branch name..."){
			$("#error").Popup("Please Enter the branch name", {type:'alert', duration:3000});
			return false;
		}
		var project = $("#project").val();
		var branch = $("input#branchname").val();
		$.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/newBranch',
			data: {project:$("input#workdir").val() + "/" + project, name:branch, create:mode},
			success: function(data){
				if(data.code == 1){
					$("input#branchname").val("Enter the branch name...");
					gitStatus();
				}
				else{
					$("#error").Popup(data.result, {type:'error'});
				}
			}
		});
		return false;
	}
	function loadBranch(branch){
		$("#activebranch").empty();
		for(i=0; i< branch.length; i++){
			selected = (branch[i].indexOf('*') == 0)? "selected":"";
			$("#activebranch").append("<option value='" + branch[i] +
				"' " + selected + ">" + branch[i] + "</option>");
		}
	}
});