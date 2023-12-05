
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



function set_url(id, base_url, tab_id = ""){ //base array has member info and tab array has all tab info for that member
    var url_text = document.getElementById("url_"+ id);
    if(tab_id == ""){
      url_text.innerHTML = base_url
    }
    else{
      url_text.innerHTML = tab_id;
    }
  }


//Function to update the tab name and image when another element is selected from drop down menu  
function update_tab(id, tab_name, tab_image){
  var button_text = document.getElementById("button_name_"+ id);
  button_text.innerHTML = tab_name;
  var preview_image = document.getElementById("preview_image_"+ id);
  preview_image.src = tab_image;
}

//Function to set the value of input ref_url in c&A.html to an array of ref_urls to submit to views.py
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


function add_to_grade_list(array_student){
  console.log(array_student);
}