/* When the user clicks on the button, 
toggle between hiding and showing the dropdown content */
function toggle_dropdown() {
  if(document.getElementById("main-account-dropdown").className == "hide-dropdown")
    document.getElementById("main-account-dropdown").className = "show-dropdown";
  else
    document.getElementById("main-account-dropdown").className = "hide-dropdown";
}
