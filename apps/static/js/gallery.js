function toggle_class_by_id(elem_id, class1, class2) {
	if(document.getElementById(elem_id).className == class1) {
		document.getElementById(elem_id).className = class2;
		console.log(1);
	} else {
		document.getElementById(elem_id).className = class1;
		console.log(2);
	}
}


function upvote(file_id) {
	var xhttp = new XMLHttpRequest();
	xhttp.onload  = function() {
		var jsonResponse = JSON.parse(this.responseText);
		document.getElementById("total-val-"+file_id).innerHTML = jsonResponse["total"];

		// Toggle between upvote selected and unselected
		toggle_class_by_id("upvote-" + file_id, "upvote", "upvote-selected")
		if(document.getElementById("downvote-" + file_id).className == "downvote-selected") {
			toggle_class_by_id("downvote-" + file_id, "downvote", "downvote-selected")
		}
	};

	xhttp.open("POST", upvote_url, true);
  	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  	xhttp.setRequestHeader("X-CSRFToken", csrf_token)
  	xhttp.send("image_id=" + file_id);
}

function downvote(file_id) {
	var xhttp = new XMLHttpRequest();
  	xhttp.onload  = function() {
		var jsonResponse = JSON.parse(this.responseText);
		document.getElementById("total-val-"+file_id).innerHTML = jsonResponse["total"];

		// Toggle between downvote selected and unselected
		toggle_class_by_id("downvote-" + file_id, "downvote", "downvote-selected")
		if(document.getElementById("upvote-" + file_id).className == "upvote-selected") {
			toggle_class_by_id("upvote-" + file_id, "upvote", "upvote-selected")
		}
	}
  	xhttp.open("POST", downvote_url, true);
  	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  	xhttp.setRequestHeader("X-CSRFToken", csrf_token)
  	xhttp.send("image_id=" + file_id);
}