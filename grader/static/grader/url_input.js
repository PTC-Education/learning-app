
//Function to enable or disable grade button based on if there are documents to grade

function checkURLs_for_enabling_grade_button() {
  var listofurlbuttons = document.getElementById("urlButtonContainer"); //open the list
  var urlbuttons_existing = listofurlbuttons.getElementsByTagName("li"); //get all the items in the list
  var urlarray_existing = Array.prototype.slice.call(urlbuttons_existing); //convert the items into array
  var x = document.getElementById("gradeButton");
  if (urlarray_existing.length > 0) {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}

//Function to validate the urlfield -
//returns true if valid url is presented
function validateForm() {
  document.getElementById("urlError").innerHTML = " "; //empty the error message when a new url is submitted
  var x = document.forms["studenturl"]["ref_url"].value;
  let regex =
    /https:\/\/[A-Za-z0-9_-]+\.onshape\.com\/documents\/[A-Za-z0-9]+\/[A-Za-z]+\/[A-Za-z0-9]+\/e\/[A-Za-z0-9]+(?:\?|$)/i;
  if (!regex.test(x)) {
    document.getElementById("urlError").innerHTML =
      "Faulty url detected. Please make sure the url is correct."; //show the error message
    document.forms["studenturl"]["ref_url"].value = "";
    return false;
  }
}

//Function to set the value of input ref_url in urlinput.html to an array of ref_urls to submit to views.py
//returns true in the end
function set_ref_url_as_array() {
  var addedurls = generate_ref_urls(); //generate  a list of urls from the buttons' ids
  var ref_url_input = document.getElementById("ref_url_edu"); //get the element of ref_url input where  we put the url array for comparison
  ref_url_input.value = addedurls; //set the value
  return true; //return true
}
//Function to generate array of existing urls from the list of urls loaded by the user through copy paste + csv upload
//return the array of ids which is the array of urls

function generate_ref_urls() {
  var listofurlbuttons = document.getElementById("urlButtonContainer"); //open the list of buttons
  var urlbuttons_existing = listofurlbuttons.getElementsByTagName("li"); //get all the items in the list of buttons with tag name "li"
  var urlarray_existing = Array.prototype.slice.call(urlbuttons_existing); //convert the items into array

  //create array of the ids of the buttons - Note: ids are the full onshape url entered by the user - unique urls=unique ids

  var addedurls = []; //create blank url array
  for (let i = 0; i < urlarray_existing.length; i++) {
    addedurls.push(urlarray_existing[i].id); //grab the id
  }
  return addedurls;
}

//Function to read contents of uploaded file - CSV file or Space separated file
function readfilecontent() {
  const fileInput = document.getElementById("csvfile"); //read file from the file upload button
  const selectedFile = fileInput.files[0]; // get the file
  let fr = new FileReader(); //initiate FileReader class
  fr.readAsText(selectedFile);

  fr.onload = () => {
    parse_list_of_url(fr.result);
  };

  fr.onerror = () => {
    console.log(fr.error);
  };
}

//Function to read contents from the url field
function show_url_as_buttons(is_scioly) {
  let urllist = document.forms["urlform"]["url"].value; //get the value in the text field
  parse_list_of_url(urllist, is_scioly);
  document.forms["urlform"]["url"].value = ""; //make text box empty
}

//Function to parse the list of url from the input form and display as closable buttons in the list with id = urlButtonContainer
function parse_list_of_url(urllist, is_scioly) {
  document.getElementById("urlError").innerHTML = " "; //empty the error message when a new url is submitted
  var urlarray = urllist.split(/,\s*|\s+/); //split the url based on space and commas
  uniqueUrls = [...new Set(urlarray)]; //get the unique urls
  
  for (let i = 0; i < uniqueUrls.length; i++) {
    //iterate over all the unique urls
    if (!uniqueUrls[i] == "") {
      //only if the url is not blank , might or might not need this
      //test urlvalidity
      if(is_scioly) {
        let regex =
          /https:\/\/[A-Za-z0-9_-]+\.onshape\.com\/documents\/[A-Za-z0-9]+(?:\?|$)/i;
        if (regex.test(uniqueUrls[i])) {
          addURLasbutton(uniqueUrls[i]); //add the valid onshape url as a button if it is a valid onshape url
        } else {
          document.getElementById("urlError").innerHTML =
            "At least one faulty URL was detected. Please make sure all the urls are formatted correctly.";
        }
      }
      else {
        let regex =
          /https:\/\/[A-Za-z0-9_-]+\.onshape\.com\/documents\/[A-Za-z0-9]+\/[A-Za-z]+\/[A-Za-z0-9]+\/e\/[A-Za-z0-9]+(?:\?|$)/i;
        if (regex.test(uniqueUrls[i])) {
          addURLasbutton(uniqueUrls[i]); //add the valid onshape url as a button if it is a valid onshape url
        } else {
          document.getElementById("urlError").innerHTML =
            "At least one faulty url was detected. Please make sure all the urls are formatted correctly.";
        }
      }
    }
  }
}

//Function to add url as a button inside the  list with id = urlButtonContainer
function addURLasbutton(toadd) {
  var listofurlbuttons = document.getElementById("urlButtonContainer"); //open the list
  var addedurls = generate_ref_urls();

  //only create new button for urls that are not already in the button div (list)
  if (!addedurls.includes(toadd)) {
    var newField = document.createElement("li"); //create an item as the list
    newField.setAttribute("id", toadd); //set the url as the id
    newField.setAttribute("name", "ref_url[]"); //set the url as the id
    listofurlbuttons.appendChild(newField); //create the list
    item = document.getElementById(toadd); //grab the new button for editing innerHTML
    did = get_did_from_url(toadd); // grab the did from the url string
    //add hyperlink
    item.innerHTML =
      '<a href="' +
      toadd +
      '"target="_blank">' +
      did +
      "</a>" +
      '<span class="close" onclick=removeUrl("' +
      toadd +
      '")>&times;</span>'; //update the content of the item with a closable icon and a js function on click
  }
  checkURLs_for_enabling_grade_button(); //Function enables or disables the Grade model button - by checking for available URLs to grade
}

// function to remove the button when clicked
function removeUrl(toremove) {
  list = document.getElementById("urlButtonContainer"); //list the items in the list
  item = document.getElementById(toremove); //find the item that needs to be removed
  list.removeChild(item); //remove from the selected item list
  checkURLs_for_enabling_grade_button(); //Function enables or disables the Grade model button - by checking for available URLs to grade
}

//function to split the url into components
function get_did_from_url(url) {
  ids = url.split("/");
  return ids[2] + " " + ids[4]; //returning the onshape link and did
}
