/* When the user clicks on the user profile button, 
toggle between hiding and showing the dropdown content */
function toggle_dropdown() {
  if(document.getElementById("main-account-dropdown").className == "hide-dropdown")
    document.getElementById("main-account-dropdown").className = "show-dropdown";
  else
    document.getElementById("main-account-dropdown").className = "hide-dropdown";
}

/* When the user clicks on the close button, 
close the specific notifications */
function close_notification(currentNode) {
  let main_content = currentNode.parentNode.parentNode.parentNode;
  let notification = currentNode.parentNode.parentNode;
  main_content.removeChild(notification);
}
