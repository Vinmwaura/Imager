function toggle_class_by_id(elem_id, class1, class2) {
	let elem = document.getElementById(elem_id);
	if(elem) {
		if(elem.className.includes(class1) == true) {
			elem.classList.remove(class1);
			elem.classList.add(class2);
		} else {
			elem.classList.remove(class2);
			elem.classList.add(class1);
		}
	}
}

function toggle_class(elem, class1, class2) {
	if(elem) {
		if(elem.className.includes(class1) == true) {
			elem.classList.remove(class1);
			elem.classList.add(class2);
		} else {
			elem.classList.remove(class2);
			elem.classList.add(class1);
		}
	}
}

function text_overflow(class_name) {
	let text_div = document.getElementsByClassName(class_name);

	for(let i=0; i<text_div.length; i++) {
		if (text_div[i].scrollWidth > text_div[i].clientWidth) {
			text_div[i].classList.add("scroll");
		}
	}
}

function upvote(image_id) {
	var xhttp = new XMLHttpRequest();
	xhttp.onload  = function() {
		var jsonResponse = JSON.parse(this.responseText);
		document.getElementById("total-val-"+image_id).innerHTML = jsonResponse["total"];

		// Toggle between upvote selected and unselected
		toggle_class_by_id("upvote-" + image_id, "upvote", "upvote-selected");
		if(document.getElementById("downvote-" + image_id).className == "downvote-selected") {
			toggle_class_by_id("downvote-" + image_id, "downvote", "downvote-selected");
		}
	};

	xhttp.open("POST", upvote_url, true);
  	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  	xhttp.setRequestHeader("X-CSRFToken", csrf_token);
  	xhttp.send("image_id=" + image_id);
}

function downvote(image_id) {
	var xhttp = new XMLHttpRequest();
  	xhttp.onload  = function() {
		var jsonResponse = JSON.parse(this.responseText);
		document.getElementById("total-val-"+image_id).innerHTML = jsonResponse["total"];

		// Toggle between downvote selected and unselected
		toggle_class_by_id("downvote-" + image_id, "downvote", "downvote-selected");
		if(document.getElementById("upvote-" + image_id).className == "upvote-selected") {
			toggle_class_by_id("upvote-" + image_id, "upvote", "upvote-selected")
		}
	}
  	xhttp.open("POST", downvote_url, true);
  	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  	xhttp.setRequestHeader("X-CSRFToken", csrf_token)
  	xhttp.send("image_id=" + image_id);
}

/* Adjusts Gallery width */
function adjust_gallery_width(margin=10, image_width=240, recursion_hack=false) {
	let gallery_container = document.getElementsByClassName('gallery-section');

	if(gallery_container) {
		// Get width of gallery window on the broswer
		gallery_width = gallery_container[0].offsetWidth;
		// console.log("Old Width: ", gallery_width)
		let maxBoxPerRow = Math.floor(gallery_width / (image_width + (margin * 2)));
		new_gallery_width = (maxBoxPerRow * (image_width + (margin * 2)));
		
		// console.log("New width: ", new_gallery_width);
		if (gallery_width == new_gallery_width && recursion_hack == false) {
			/* Hack to make gallery resize when screen size increases */
			gallery_container[0].style.width = "100%"
			adjust_gallery_width(margin, image_width, true);
		} else {
			gallery_container[0].style.width = new_gallery_width + 'px';
		}
	}
}

/* Adds hidden inputs in the form */
function add_hidden_inputs(parent_elem_id, name, args) {
	let hidden_input = document.createElement("input");
	hidden_input.setAttribute("type", "hidden");
	hidden_input.setAttribute("name", name);
	hidden_input.setAttribute("id", name);
	hidden_input.setAttribute("value", args);

	// Append to form element.
	let form_elem = document.getElementById(parent_elem_id);
	form_elem.appendChild(hidden_input);
}

/* Removes hidden inputs in the form */
function remove_hidden_inputs(elem_id) {
	let input_elem = document.getElementById(elem_id);
	// Removes element.
	input_elem.remove();
}

/* Updates number of selected images to be deleted */
function count_selected_items() {
	let selected_images = document.getElementsByClassName(
		"gallery-select-individual");
	if (selected_images.length > 0) {
		// Update counter with checked checkbox
		let count = 0;
		for (let i=0; i<selected_images.length; i++) {
			if( selected_images[i].checked) {
				count = count + 1;
			}
		}
		document.getElementById("delete-count").innerHTML = count;

		if (count == 0) {
			toggle_delete();
		}
	}
}

/* Toggles select multiple checkbox option */
function toggle_delete(image_id) {
	if (image_id) {
		let checkbox = document.getElementById('checkbox-' + image_id);
		if(checkbox) {
			checkbox.checked = true;
			count_selected_items()
		}	
	}

	let form_container = document.getElementById("form-container");
	toggle_class(form_container, "show", "hide");

	let select_gallery = document.getElementsByClassName('checkbox-section');
	if(select_gallery) {
		for(let i=0; i<select_gallery.length; i++) {
			toggle_class(select_gallery[i], "show", "hide");
		}	
	}
}

/* Append hiddent inputs to forms before submitting */
function pre_submit() {
	args = "";
	let select_gallery = document.getElementsByClassName('gallery-select-individual');
	if(select_gallery) {
		image_obj = [];
		for(let i=0; i<select_gallery.length; i++) {
			if( select_gallery[i].checked) {
				image_obj.push(select_gallery[i].value);
			}
		}
		args = image_obj.join(",");
	}

	// Appends hidden input to form.
	add_hidden_inputs("delete-form", "image_id", args);
}