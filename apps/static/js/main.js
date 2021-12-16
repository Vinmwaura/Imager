/* When the user clicks on the close button, 
close the specific notifications */
function close_notification(currentNode) {
  let main_content = currentNode.parentNode.parentNode.parentNode;
  let notification = currentNode.parentNode.parentNode;
  main_content.removeChild(notification);
}
