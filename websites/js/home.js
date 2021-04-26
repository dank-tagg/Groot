function dark_mode(bool) {
    return bool ? yes:no
}

function openNav() {
  document.getElementById("sidebar").style.width = "200px";
  document.getElementById("main").style.marginLeft = "200px";
}


/* Set the width of the sidebar to 0 and the left margin of the page content to 0 */
function closeNav() {
  document.getElementById("sidebar").style.width = "0";
  document.getElementById("main").style.marginLeft = "0";
}