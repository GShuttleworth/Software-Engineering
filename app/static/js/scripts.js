//global?
var refreshrate = 2000;
function refresh() {
	$.ajax({
		type : 'POST',
		url : "/refresh",
		success: function(d) {
			var data = JSON.parse(d);
			mode(data.mode);
			live(data.live);
			updatedash(data.anomaly,data.trades,data.tradevalue);
			//update anomalies
			for(var i in data.anomalies){
				var anomaly = data.anomalies[i];
				//create htmls for each
				anomalyHTML(anomaly.id,anomaly.date,anomaly.time,anomaly.type,anomaly.action);
			}
		},
		error: function(d) {
			console.log("server down");
			//error bar here
		}
	});
	//for testing, stop this fucking refreshing
	setTimeout(refresh, refreshrate); // you could choose not to continue on failure...
}

function live(status) {
	if(status==true){
		
	}else{
		
	}
}
function mode(status) {
	if(status==1){
		$('#live').html('Live Data');
	}else{
		$('#live').html('Historical Data');
	}
}

function updatedash(anomalycount,tradecount,tradevalue) {
	$('#trades').html(tradecount);
	$('#anomalies').html(anomalycount);
	$('#tradevalue').html('&pound;'+tradevalue);

}

function loadanomalies(){
	$.ajax({
		type : 'POST',
		url : "/getanomalies",
		success: function(d) {
		//TODO turn result into html
		   var data = JSON.parse(d);
		   for(var i in data.anomalies){
			   var anomaly = data.anomalies[i];
			   //create htmls for each
			   anomalyHTML(anomaly.id,anomaly.date,anomaly.time,anomaly.type,anomaly.action);
		   }
		},
		error: function(d) {
		   console.log("unable to get anomalies");
		   //error bar here
		}
	});
}

function changerefresh(rate){
	refreshrate=rate;
	alert("refresh rate changed to: "+rate);
}
function anomalyHTML(id,date,time,type,action){
	//generates html for anomaly specified (just adds to html table)
	var table = document.getElementById("table-anomaly");
	var rowCount = table.rows.length;
	var row = table.insertRow(rowCount);
	var cell_id = row.insertCell(0);
	var cell_date = row.insertCell(1);
	var cell_time = row.insertCell(2);
	var cell_type = row.insertCell(3);
	var cell_action = row.insertCell(4);
	cell_id.innerHTML = id;
	cell_date.innerHTML = date;
	cell_time.innerHTML = time;
	//convert type int to something appropriate
	
	cell_type.innerHTML = convert_type(type);
	cell_action.innerHTML = '<a href="/stock/'+action+'/anomaly/'+id+'"><button type="button" class="btn btn-primary">Action</button></a>';
}

function convert_type(t){
	var type="Unknown";
	switch(t){
		case 1:
			type="Fat finger"
			break;
		case 2:
			type="Bear raids"
			break;
		case 3:
			break;
	}
	return type;
}

function togglemode(mode){
	var data = {"mode":mode};
	$.ajax({
		type : 'POST',
		url : "/toggle",
		data : JSON.stringify(data),
		contentType: 'application/json;charset=UTF-8',
		success: function(d) {
			
		},
		error: function(d) {
			console.log("unable to switch");
			//error bar here
		}
	});
}
function init_session(){
	$.ajax({
	   type : 'POST',
	   url : "/session",
	   success: function(d) {
		
	   },
	   error: function(d) {
		   console.log("session cannot initialise");
	   }
   });
}
$(document).ready(function() {
	// run the first time; all subsequent calls will take care of themselves
	init_session();
	refresh();
	//load anomalies
	loadanomalies();
	
	//event listeners
	$("#btn-live").click(function(e){
		e.preventDefault();
		//alert("hi");
		togglemode(1);
	});
	$("#btn-historical").click(function(e){
	   e.preventDefault();
	   //alert("hi");
	   togglemode(0);
	   //import file
   });
});
