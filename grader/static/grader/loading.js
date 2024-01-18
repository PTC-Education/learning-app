//TO FIX : make calls with the div class name as argument

function loading_index() {
    var lists = document.getElementsByClassName("info_list"); 
    for (var i = 0; i < lists.length; i++) {
        lists[i].innerHTML = "<div class=\"loader\"></div>"; 
    }
}

function loading_list() {
    const main_content = document.getElementById("lists"); 
    main_content.innerHTML = "<div class=\"loader\"></div>"; 
}

function loading_spinner(divid) {
    const main_content = document.getElementById(divid); 
    main_content.innerHTML = "<div class=\"loader\"></div>"; 
}

function loading_spinner_results(divid) {
    console.log("spinner " + divid)
    const main_content = document.getElementById(divid); 
    main_content.innerHTML = "<div class=\"loader smaller_loader\"></div>"; 
}

function loading_documentlist() {
    const main_content = document.getElementById("documentlists"); 
    main_content.innerHTML = "<div class=\"loader\"></div>"; 
}