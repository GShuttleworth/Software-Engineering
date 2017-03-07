//global?
function refresh() {
	$.ajax({
		type : 'POST',
		url : "/refresh",
		success: function(d) {
			var data = JSON.parse(d);
			//console.log(data);
			mode(data.mode);
			live(data.live);
			updatedash(data.anomaly,data.trades,data.tradevalue);
			//update anomalies
			for(var i in data.anomalies){
				var anomaly = data.anomalies[i];
				if(parseInt(anomaly.type)!=0){
					//create htmls for each
					anomalyHTML(anomaly.id,anomaly.date,anomaly.time,anomaly.type,anomaly.action);
				}else if(parseInt(anomaly.type)==0){
					//make sure it actually does exist
					anomalyHTMLremove(anomaly.id);
				}
			}
		},
		error: function(d) {
			console.log("server down");
			//error bar here
			//make it stop refreshing
			clearTimeout(refresher);
		}
	});
	//for testing, stop this fucking refreshing
	refresher=setTimeout(refresh, refreshrate); // you could choose not to continue on failure...
}

function updatedash(anomalycount,tradecount,tradevalue) {
	$('#trades').html(tradecount);
	$('#anomalies').html(anomalycount);
	$('#tradevalue').html('&pound;'+nFormatter(tradevalue,2));
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

function dismiss(id){
	$.ajax({
		type : 'POST',
		url : "/dismiss",
		data : JSON.stringify(id),
		contentType: 'application/json;charset=UTF-8',
		success: function(d) {
		   //just dismiss here because quicker?
		   anomalyHTMLremove(anomaly.id);
		},
		error: function(d) {
		
		}
   });
}
function anomalyHTMLremove(id){
	var table = $('#table-anomaly').DataTable();
	table.row($("#tbl-row-"+id)).remove().draw();
	
	alertify.logPosition("top right");
	alertify.error('Anomaly Dismissed');
}
function anomalyHTML(id,date,time,type,action){

	// Make date human readable
	var humanTime = time.substring(0,8);
	var humanDate = moment(date).format('DD-MM-YYYY');

	// Init Datatable
	var table = $('#table-anomaly').DataTable();
	// Construct HMTL for table row
	var row = "<tr id='tbl-row-"+id+"'><td>"+id+"</td><td>"+humanDate+"</td><td>"+humanTime+"</td><td>"+convert_type(type)+"</td><td><div class='btn-group' role='group' aria-label=''...''><a href='/stock/"+action+"/anomaly/"+id+"'><button type='button' class='btn btn-primary'>View</button></a> <a href='#'><button type='button' class='btn btn-success' onclick='dismiss("+id+")'>Dismiss</button></a></div>";
	table.row.add( $(row)[0] ).draw();
	alertify.logPosition("top right");
	alertify.success("New Anomaly Detected");
	beep();
}

function cleartable(){
	var table = $('#table-anomaly').DataTable();
 
	table.clear().draw();
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
			type="Price spike"
			break;
		case 4:
			type="Volume spike"
			break;
	}
	return type;
}

function init_session(){
	$.ajax({
	   type : 'POST',
	   url : "/session",
	   success: function(d) {
			refresh();
	   },
	   error: function(d) {
		   console.log("session cannot initialise");
	   }
   });
}
function beep() {
	var snd = new Audio("data:audio/wav;base64,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qJrx4KOQjahZxWbcZgztj2c49nKmkId44S71j0c8eV9yDK6uPRzx5X18eDvjvQ6yKo9ZSS6l//8elePK/Lf//IInrOF/FvDoADYAGBMGb7FtErm5MXMlmPAJQVgWta7Zx2go+8xJ0UiCb8LHHdftWyLJE0QIAIsI+UbXu67dZMjmgDGCGl1H+vpF4NSDckSIkk7Vd+sxEhBQMRU8j/12UIRhzSaUdQ+rQU5kGeFxm+hb1oh6pWWmv3uvmReDl0UnvtapVaIzo1jZbf/pD6ElLqSX+rUmOQNpJFa/r+sa4e/pBlAABoAAAAA3CUgShLdGIxsY7AUABPRrgCABdDuQ5GC7DqPQCgbbJUAoRSUj+NIEig0YfyWUho1VBBBA//uQZB4ABZx5zfMakeAAAAmwAAAAF5F3P0w9GtAAACfAAAAAwLhMDmAYWMgVEG1U0FIGCBgXBXAtfMH10000EEEEEECUBYln03TTTdNBDZopopYvrTTdNa325mImNg3TTPV9q3pmY0xoO6bv3r00y+IDGid/9aaaZTGMuj9mpu9Mpio1dXrr5HERTZSmqU36A3CumzN/9Robv/Xx4v9ijkSRSNLQhAWumap82WRSBUqXStV/YcS+XVLnSS+WLDroqArFkMEsAS+eWmrUzrO0oEmE40RlMZ5+ODIkAyKAGUwZ3mVKmcamcJnMW26MRPgUw6j+LkhyHGVGYjSUUKNpuJUQoOIAyDvEyG8S5yfK6dhZc0Tx1KI/gviKL6qvvFs1+bWtaz58uUNnryq6kt5RzOCkPWlVqVX2a/EEBUdU1KrXLf40GoiiFXK///qpoiDXrOgqDR38JB0bw7SoL+ZB9o1RCkQjQ2CBYZKd/+VJxZRRZlqSkKiws0WFxUyCwsKiMy7hUVFhIaCrNQsKkTIsLivwKKigsj8XYlwt/WKi2N4d//uQRCSAAjURNIHpMZBGYiaQPSYyAAABLAAAAAAAACWAAAAApUF/Mg+0aohSIRobBAsMlO//Kk4soosy1JSFRYWaLC4qZBYWFRGZdwqKiwkNBVmoWFSJkWFxX4FFRQWR+LsS4W/rFRb/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////VEFHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAU291bmRib3kuZGUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMjAwNGh0dHA6Ly93d3cuc291bmRib3kuZGUAAAAAAAAAACU=");
	if(sound==true){
		snd.play();
	}
}

$(document).ready(function() {
	//load anomalies
	$('#table-anomaly').DataTable( {
		"columnDefs": [
    { "orderable": false, "targets": 4 }
  ]
	});
	loadanomalies();
});
