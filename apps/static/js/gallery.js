function delay(callback, ms) {
   	var timer = 0;
   	return function() {
      	var context = this,
         	args = arguments;
      	clearTimeout(timer);
      	timer = setTimeout(function() {
         	callback.apply(context, args);
      	}, ms || 0);
   };
}

/* Toggles suggestion section when user enters value */
function toggle_suggestion() {
    let suggestion_elem = document.getElementById("search-dropdown");
    if(suggestion_elem!=undefined) {
    	suggestion_elem.classList.toggle("hide-search-dropdown");
	    suggestion_elem.classList.toggle("show-search-dropdown");	
    }
}

function open_suggestion() {
	// Toggle Search Dropdown if closed.
    let suggestion_elem = document.getElementById("search-dropdown");
    if(suggestion_elem!=undefined) {
	    if (suggestion_elem.classList.contains("hide-search-dropdown")) {
	        toggle_suggestion();
	    }
	}
}

function close_suggestion() {
	// Toggle Search Dropdown if opened.
    let suggestion_elem = document.getElementById("search-dropdown");
    if(suggestion_elem!=undefined) {
	    if (suggestion_elem.classList.contains("show-search-dropdown")) {
	        toggle_suggestion();
	    }
	}
}

// Highlights search text
function highlight(search_val, text) {
	let searchRegExp = new RegExp(search_val, "gi");
	// Uses RegExp.lastMatch hack to replace word with highlighed span element.
	let new_text = text.replace(searchRegExp, "<span class='highlight'>$&</span>");
	return new_text
}

// Search functionality
function search_result(search_val, search_url, gallery_img, gallery_user) {
	search_results = document.getElementById("search-dropdown");

	var xhr = new XMLHttpRequest();
	xhr.open("GET", search_url+search_val, true);

	xhr.onload = function () {
		// Request finished. Do processing here.
		var jsonResponse = JSON.parse(this.responseText);

		search_html = "";
		if (jsonResponse.results.image.length > 0 || jsonResponse.results.tags.length > 0 || jsonResponse.results.users.length > 0)  {
			
			search_html += "<strong>IMAGE</strong><br>";
			search_html += "<hr>"
			search_html += "<ul>"
			for(let i=0; i<jsonResponse.results.image.length; i++) {
				img_id = jsonResponse.results.image[i].image_id;
				image_title = jsonResponse.results.image[i].title;
				search_html += '<a href=' + gallery_img + img_id + '><li>' + highlight(search_val, image_title) + '</li></a>';
			}
			search_html += "</ul>"
			
			search_html += "<strong>TAGS</strong><br>";
			search_html += "<hr>"
			search_html += "<ul>"
			for(let i=0; i<jsonResponse.results.tags.length; i++) {
				tagname = jsonResponse.results.tags[i].tagname;
				search_html += '<li>' + highlight(search_val, tagname) + '</li>';
			}
			search_html += "</ul>"
			
			search_html += "<strong>USERS</strong><br>";
			search_html += "<hr>"
			search_html += "<ul>"
			for(let i=0; i<jsonResponse.results.users.length; i++) {
				username = jsonResponse.results.users[i].username;
				search_html += '<a href=' + gallery_user + username + '><li>' + highlight(search_val, username) + '</li></a>';
			}
			search_html += "</ul>";
		} else {
			// Hide if no result found.
			search_html += "<h1 style='text-align: center'>No data found!</h1>";
		}
		search_results.innerHTML = search_html;
	};

	xhr.send();
}

function suggest(input_val, search_url, gallery_img, gallery_user) {
	if (input_val == '') {
		// Hide suggestion.
		suggestion_elem = document.getElementById("search-dropdown");
		if(suggestion_elem != undefined) {
			toggle_suggestion();
		}
	} else {
		search_result(input_val, search_url, gallery_img, gallery_user);
		// Show suggestion if hidden initially.
		suggestion_elem = document.getElementById("search-dropdown");
		if(suggestion_elem != undefined) {
			if(suggestion_elem.classList.contains('hide-search-dropdown')) {
				toggle_suggestion()
			}
		}
	}
}

// Picture Modal
function load_picture_modal(pic) {
	let image_modal = document.getElementById("image-modal");
	let image_elem = document.getElementById("image-original");

	original_pic = pic.querySelector("img");
	if (original_pic) {
		image_elem.src = original_pic.src;
		image_elem.alt = original_pic.alt;

		image_modal.classList.toggle("show-modal");
		original_pic.classList.toggle("hide-image-panel");
	}
}

function close_picture_modal() {
	let image_modal = document.getElementById("image-modal");
	let image_elem = document.getElementById("image-original");

	let original_pic = document.getElementById("image-panel")
	original_pic = original_pic.querySelector("img");

	image_elem.src = "#";
	image_elem.alt = " ";

	image_modal.classList.toggle("show-modal");
	original_pic.classList.toggle("hide-image-panel");
}

// Enables text to scroll when text overflow detected.
function text_overflow(text_div) {
	for(let i=0; i<text_div.length; i++) {
		if (text_div[i].scrollWidth > text_div[i].clientWidth) {
			text_div[i].classList.add("scroll");
		}
	}
}

// Sends upvotes data to server.
function upvote(upvote_elem, upvote_url) {
	if (upvote_elem) {
		let image_id = upvote_elem.id.replace("upvote-", "");
		let csrf_token = document.querySelector('meta[name="csrf-token"]').content;

		var xhttp = new XMLHttpRequest();
		xhttp.open("POST", upvote_url, true);
	  	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	  	xhttp.setRequestHeader("X-CSRFToken", csrf_token);
	  	xhttp.send("image_id=" + image_id);

	  	xhttp.onload  = function() {
			var jsonResponse = JSON.parse(this.responseText);

			// Updates total score for image
			let total_score = document.getElementById("total-val-"+image_id);
			if (total_score) {
				total_score.innerHTML = jsonResponse["total"];
			}

			// Unselects downvote if already toggled.
			let downvote_elem = document.getElementById("downvote-" + image_id);
			if ( downvote_elem.classList.contains("downvote-selected") ) {
				downvote_elem.classList.toggle("downvote-selected");
				downvote_elem.classList.toggle("downvote");
			}
			// Toggles upvote.
			upvote_elem.classList.toggle("upvote");
			upvote_elem.classList.toggle("upvote-selected")
		};
	}
}

function downvote(downvote_elem, downvote_url) {
	if (downvote_elem) {
		let image_id = downvote_elem.id.replace("downvote-", "");
		let csrf_token = document.querySelector('meta[name="csrf-token"]').content;

		var xhttp = new XMLHttpRequest();
		xhttp.open("POST", downvote_url, true);
	  	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	  	xhttp.setRequestHeader("X-CSRFToken", csrf_token);
	  	xhttp.send("image_id=" + image_id);

	  	xhttp.onload  = function() {
			var jsonResponse = JSON.parse(this.responseText);

			// Updates total score for image
			let total_score = document.getElementById("total-val-" + image_id);
			if (total_score) {
				total_score.innerHTML = jsonResponse["total"];
			}

			// Unselects upvote if already toggled.
			let upvote_elem = document.getElementById("upvote-" + image_id);
			if ( upvote_elem.classList.contains("upvote-selected") ) {
				upvote_elem.classList.toggle("upvote-selected");
				upvote_elem.classList.toggle("upvote");
			}
			// Toggles downvote.
			downvote_elem.classList.toggle("downvote")
			downvote_elem.classList.toggle("downvote-selected");
		};
	}
}

/* Adjusts Gallery width */
function adjust_gallery_width(gallery_container, margin=10, image_width=240, recursion_hack=false) {
	if (gallery_container) {
		// Get width of gallery window on the broswer
		gallery_width = gallery_container.offsetWidth;
		//console.log("Old Width: ", gallery_width)
		let maxBoxPerRow = Math.floor(gallery_width / (image_width + (margin * 2)));
		new_gallery_width = (maxBoxPerRow * (image_width + (margin * 2)));
		//console.log("New width: ", new_gallery_width);
		if (gallery_width == new_gallery_width && recursion_hack == false) {
			/* Hack to make gallery resize when screen size increases */
			gallery_container.style.width = "100%"
			adjust_gallery_width(gallery_container, margin, image_width, true);
		} else {
			gallery_container.style.width = new_gallery_width + 'px';
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
			toggle_delete(null);
		}
	}
}

/* Toggles select multiple checkbox option */
function toggle_delete(elem) {
	if (elem) {
		let image_id = elem.id.replace("delete-", "");

		let checkbox = document.getElementById('checkbox-' + image_id);
		if(checkbox) {
			checkbox.checked = true;
			count_selected_items()
		}	
	}

	let form_container = document.getElementById("form-container");
	form_container.classList.toggle("show");
	form_container.classList.toggle("hide");

	let select_gallery = document.getElementsByClassName('checkbox-section');
	if(select_gallery) {
		for(let i=0; i<select_gallery.length; i++) {
			select_gallery[i].classList.toggle("show");
			select_gallery[i].classList.toggle("hide");
		}	
	}
}

/* Append hidden inputs to forms before submitting */
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
