$(document).ready( function() {
	var send = false;	
	gitStatus();
	$("#project").change(function(){		
		if (send){
			getStatus.abort();
			send=false;
		}
		gitStatus();
	});
	$("#activebranch").change(function(){
		
	});
	$("#addbranch").click(function(){
		if($("input#branchname").val() == "" || 
			$("input#branchname").val() == "Enter the branch name..."){
			error("Error: Please Enter your branch name");
			return false;
		}
		alert($("input#branchname").val());
		return false;
	});
	$("#commit").click(function(){
		if($("input#commitmsg").val() == "" ||
			$("input#commitmsg").val() == "Enter message..."){
			error("Error: Please Enter the commit message");
			return false;
		}
		alert($("input#commitmsg").val());
		return false;
	});
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
		getStatus = $.ajax({
			type: "POST",
			url: $SCRIPT_ROOT + '/getProjectStatus',
			data: "project=" + $("input#workdir").val() + "/" + project,
			success: function(data){				
				if(data.code == 1){
					$("#branchlist").show();
					$("#status").append("<h2>Your Repository status</h2>");					
					message = data.result.split('\n').join('<br/>');
					//alert(message);
					$("#status").append("<p>" + message + "</p>");
					loadBranch(data.branch);
					if(data.dirty){
						$("#push").show();
					}
				}
				else{
					$("#flash").append("<ul class='flashes'><li>Error: " + data.result + "</li></ul>");
				}
			}
		});
	}
	function loadBranch(branch){
		$("#activebranch").empty();
		for(i=0; i< branch.length; i++){
			selected = (branch[i].indexOf('*') == 0)? "selected":"";
			$("#activebranch").append("<option value='" + branch[i] +
				"'>" + branch[i] + "</option>");
		}
	}
	
	function error(msg){
		$("#flash").fadeOut('normal');
		$("#flash").empty();
		$("#flash").fadeIn('normal');
		$("#flash").append("<ul class='flashes'><li>" + msg + "</li></ul>");
	}
});