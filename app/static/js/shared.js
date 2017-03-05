//global?
var refreshrate = 2000;
var sound=false;
var refresher;
function live(status) {
	if(status==true){
		$("#btn-connect").html('<i class="fa fa-plug fa-fw"></i> Disconnect');
		$("#live-status").html('Stream status: connected');
	}else{
		$("#btn-connect").html('<i class="fa fa-plug fa-fw"></i> Connect');
		$("#live-status").html('Stream status: disconnected');
	}
}
function mode(status) {
	if(status==1){
		$('#live').html('Live Data');
	}else{
		$('#live').html('Historical Data');
	}
}

function changerefresh(rate){
	refreshrate=rate;
	//alert("refresh rate changed to: "+rate);
}

function toggleconnect(){
	$.ajax({
		type : 'POST',
		url : "/connect",
		contentType: 'application/json;charset=UTF-8',
		success: function(d) {
		success = JSON.parse(d);
			if(success.change==true){
			   //alert("toggled");
			}
		},
		error: function(d) {
			console.log("unable to switch");
			//error bar here
		}
	});
}
function togglemode(mode){
	var data = {"mode":mode};
	$.ajax({
		type : 'POST',
		url : "/toggle",
		data : JSON.stringify(data),
		contentType: 'application/json;charset=UTF-8',
		success: function(d) {
			success = JSON.parse(d);
			if(success.change==false){
				alert("Already in live mode!");
			}
		},
		error: function(d) {
			console.log("unable to switch");
			//error bar here
		}
	});
}
function nFormatter(num, digits) {
	//http://stackoverflow.com/questions/9461621/how-to-format-a-number-as-2-5k-if-a-thousand-or-more-otherwise-900-in-javascrip
	num=parseFloat(num);
	var si = [
			  { value: 1E18, symbol: "E" },
			  { value: 1E15, symbol: "P" },
			  { value: 1E12, symbol: "T" },
			  { value: 1E9,  symbol: "B" },
			  { value: 1E6,  symbol: "M" },
			  { value: 1E3,  symbol: "k" }
			  ], rx = /\.0+$|(\.[0-9]*[1-9])0+$/, i;
	for (i = 0; i < si.length; i++) {
		if (num >= si[i].value) {
			return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
		}
	}
	return num.toFixed(digits).replace(rx, "$1");
}

/* Open */
function openNav(id) {
	$(".overlay-content").height(300);
	$("#upload-container").hide();
	$("#"+id).show();
	
}

/* Close */
function closeNav(id) {
	$("#"+id).hide();
}

function upload() {
	var bar = $('.bar');
	var percent = $('.percent');
	$("#uploadform").ajaxForm({
		beforeSubmit: function() {
			var percentVal = '0%';
			bar.width(percentVal)
			percent.html(percentVal);
		},
		uploadProgress: function(event, position, total, percentComplete) {
			var percentVal = percentComplete + '%';
			bar.width(percentVal)
			percent.html(percentVal);
		},
		success: function() {
			var percentVal = '100%';
			bar.width(percentVal)
			percent.html(percentVal);
		},
		complete: function(xhr) {
			if(xhr.responseText){
				alert("File uploaded");
			}
		}
	});
}
function changecookie(name,value){
	if (!!$.cookie(name)) {
		// have cookie
		$.cookie(name, value);
	} else {
		// no cookie
		$.cookie(
				 name,
				 value,
				 {
				 // The "expires" option defines how many days you want the cookie active. The default value is a session cookie, meaning the cookie will be deleted when the browser window is closed.
				 expires: 7,
				 // The "path" option setting defines where in your site you want the cookie to be active. The default value is the page the cookie was defined on.
				 path: '/'
				 }
		);
	}
}

function processfile(){
	//process the last uploaded file
	//TODO
	closeNav("uploadnav");
}
function loadstatic(){
	//load data from static database
	//TODO
	closeNav("uploadnav");
}

function displayupload(){
	//displays upload container
	$(".overlay-content").animate({height:400},200);;
	$("#upload-container").show();
	
}
function loadcookies(){
//load user cookie settings
	if (!!$.cookie("sound")) {
		sound = ($.cookie("sound")=='true');
		if(sound==true){
			document.getElementById("settings-sound").checked = true;
		}
	}
	if (!!$.cookie("refresh")) {
		refreshrate=$.cookie("refresh");
		$('select option[value='+refreshrate/1000+']').attr("selected",true);
	}
}
$(document).ready(function() {
	// run the first time; all subsequent calls will take care of themselves
	init_session();
	loadcookies();
	//event listeners
	$("#btn-connect").click(function(e){
		e.preventDefault();
		//alert("hi");
		toggleconnect();
	});
	$("#btn-historical").click(function(e){
	   e.preventDefault();
	   openNav("uploadnav");
	   //document.getElementById("data_file").click();
	   //alert("hi");
	   //togglemode(0);
	   //import file
	});
	$("#btn-settings").click(function(e){
		e.preventDefault();
		openNav("settingsnav");
	});
	$("#settings-sound").change(function() {
		if($(this).is(':checked')==true){
			sound=true;
			//save cookie
			changecookie("sound",true);
		}else{
			sound=false;
			changecookie("sound",false);
		}
	});
	$("#settings-refresh").change(function() {
		changecookie("refresh",$("#settings-refresh").val()*1000);
		changerefresh($("#settings-refresh").val()*1000)
	});
				
	$("#browse").click(function(e){
		document.getElementById("data_file").click();
	});
	$("#btn-reset").click(function(e){
		e.preventDefault();
		if (confirm("Are you sure you want to reset counters and delete all previous database trades")) {
			$.ajax({
				type: 'POST',
				url: "/reset",
				success: function(data){
				   //TODO optimise user perception
				   if(data=="ok"){
					   alert("Counters reset");
				   }else{
					   alert("Failed");
				   }
				},
				error: function(jqXHR, textStatus, errorThrown){
				   console.log("fail");
				}
			});
	   }
	});
});
