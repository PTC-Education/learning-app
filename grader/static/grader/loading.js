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

function loading_grades() {
    const main_content = document.getElementById("grades"); 
    main_content.innerHTML = "<div class=\"loader\"></div>"; 

}

function loading_documentlist() {

    const main_content = document.getElementById("documentlists"); 
    main_content.innerHTML = "<div class=\"loader\"></div>"; 

}