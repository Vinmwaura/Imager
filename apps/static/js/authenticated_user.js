/* When the user clicks on the user profile button, 
toggle between hiding and showing the dropdown content */
function toggle_dropdown() {
    let account_dropdown = document.getElementById("main-account-dropdown");
    account_dropdown.classList.toggle("hide-dropdown");
    account_dropdown.classList.toggle("show-dropdown");
}

document.onclick = function(event) {
    // Toggle Dropdown off if opened.
    let account_dropdown = document.getElementById("main-account-dropdown");
    if (account_dropdown.classList.contains("show-dropdown")) {
        if (!event.target.closest(".main-account-options")) {
            toggle_dropdown();
        }
    }
}