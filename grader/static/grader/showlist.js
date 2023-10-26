function toggleView(divid,buttonid) {
  var x = document.getElementById(divid);
  if (x.style.display === "none") {
    x.style.display = "block";
    document.getElementById(buttonid).className = "button-expanded"
    
  } else {
    x.style.display = "none";
    
    document.getElementById(buttonid).className = "button-collapsed"
  }
}

