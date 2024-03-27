// Assignment description box
function move_popup(e) {
  var div = document.getElementById('description_assignment');
  var y = e.clientY + window.scrollY;
  var windowHeight = window.innerHeight;
  var bottomThreshold = 160; 
  if (windowHeight - e.clientY < bottomThreshold) {
      // If mouse is near the bottom of the page, show div above the mouse position
      div.style.top = (y - div.offsetHeight - 25) + 'px';
  } else {
      // Otherwise, show div below the mouse position
      div.style.top = y + 15 + 'px';
  }
}

  //Function to show pop up
  function show_popup_assignment(popup, msg1, msg2){
    var reasons = document.getElementById(popup);
    reasons.style.display = "block"; 
    var date = document.getElementById("date");
    var text = document.getElementById("description_text");
    var localDateTime = new Date(msg1);
    date.innerHTML = localDateTime;
    text.innerHTML = msg2;
  }

  //Function to  hide pop up
  function hide_popup_assignment(popup){
    var reasons = document.getElementById(popup);
    reasons.style.display = "none";
  }
   
    //Function to show pop up
  function show_popup_member(popup, msg1, msg2){
    var reasons = document.getElementById(popup);
    reasons.style.display = "block"; 
    var url = document.getElementById("url_member");
    var text = document.getElementById("details_member");
    url.innerHTML = msg1;
    text.innerHTML = msg2;
  }

  //Function to  hide pop up
  function hide_popup_member(popup){
    var reasons = document.getElementById(popup);
    reasons.style.display = "none";
  }

function set_url(id, url){ //base array has member info and tab array has all tab info for that member
    var url_text = document.getElementById("url_"+ id);
      url_text.innerHTML = url;
  }

//Function to update the tab name and image when another element is selected from drop down menu  
function update_tab(id, tab_name, tab_image){
  var button_text = document.getElementById("button_name_"+ id);
  button_text.innerHTML = tab_name;
  var preview_image = document.getElementById("preview_image_"+ id);
  preview_image.src = tab_image;
}

//Function to set the value of input ref_url in c_and_a.html to an array of ref_urls to submit to views.py
//returns true in the end
function form_ref_url_array(){
  var url_array = [];
  var urls = document.getElementsByName('doc_url'); // grab the part information within all parts
			for (let i = 0; i < urls.length ; i++){
        url_array.push(urls[i].innerHTML);
      }
  url_array = url_array.join(",");
  url_box = document.getElementById("ref_url_edu");
  url_box.value = url_array;
  return true; //return true
}

//Function to check if the number of assignment is greater than 0, only submit to get asignment details 
//if there is assignment to check
function check_assignments(assignment_count){
 if (assignment_count == 0){

  return false;
 }
 else{
  return true;
 }
}


function add_to_grade_list(id){

  //get data from required action table
  const sourceRow = document.getElementById("tab_" + id);
  let source_user = sourceRow.cells[0].innerHTML;
  let source_doc = sourceRow.cells[1].innerHTML;
  let source_url = sourceRow.cells[2].innerHTML;
  let source_part = document.getElementById("button_name_" + id).innerHTML;
  let source_thumbnail = document.getElementById("preview_image_" + id).src;

  sourceRow.remove(); //remove the row from required action table

  //add a new row to the submitted work table
  var submitTable = document.getElementById('submitted_work');
  let row = submitTable.insertRow(-1); // We are adding at the end
   
  // Create new cells
  let user = row.insertCell(0);
  let doc = row.insertCell(1);
  let url = row.insertCell(2);
  let part = row.insertCell(3);
  let thumbnail_cell = row.insertCell(4);

  // add properties to the new cells
  user.innerHTML = source_user;
  user.classList.add("set_to_left_in_table");
  user.classList.add("small_font_td");

  doc.innerHTML = source_doc;
  doc.classList.add("set_to_left_in_table");
  doc.classList.add("small_font_td");

  url.innerHTML = source_url;
  url.setAttribute("name","doc_url"); //= "doc_url";
  url.hidden = true ;
  url.id = "url_" + id;

  part.innerHTML = source_part;
  part.classList.add("set_to_left_in_table");
  part.classList.add("small_font_td");

  var img = document.createElement('img');
  img.src = source_thumbnail;
  img.id = "preview_image_" + id;
  thumbnail_cell.appendChild(img);


  //function to check the content of submitted table to show 
  check_submitted_content();
  //function to check the content of required action to hide if blank
  check_required_action_content();
}


function check_required_action_content(){
  required_action_table = document.getElementById("action_required_work");
  if(required_action_table.rows.length == 1){ //if there is only one row left
    document.getElementById("action_required_box").hidden = true; //hide the enitre box with the table
  }
}

function check_submitted_content(){
  submitted_table = document.getElementById("submitted_work");
  
  if(submitted_table.rows.length == 1){ //if there is only one row left
    document.getElementById("submitted_box").hidden = true; //hide the enitre box with the table
    var error_text = document.getElementById("submission_error");
    error_text.style.display = "block";
    error_text.innerHTML = "No submissions detected for grading. ";
    console.log("done");
  }
  else{
    document.getElementById("submitted_box").hidden = false; //show the enitre box with the table
    var error_text = document.getElementById("submission_error");
    error_text.innerHTML = "";
    console.log("no submission error");
    error_text.style.display = "none";
  }

}