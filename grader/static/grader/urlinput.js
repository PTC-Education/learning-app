//Runs on load to ensure url is shown and csv is hidden
function checkURLs_for_enabling_grade_button() {
  var listofurlbuttons = document.getElementById('urlButtonContainer');         //open the list 
  var urlbuttons_existing = listofurlbuttons.getElementsByTagName("li");        //get all the items in the list
  var urlarray_existing = Array.prototype.slice.call(urlbuttons_existing);        //convert the items into array
  var x = document.getElementById("gradeButton");
  if(urlarray_existing.length>0){
   
    x.style.display = "block";
  }
  else{
    x.style.display = "none";
  }
}



//This function will toggle the view of the div when called

//Argument:
//ids of the div to toggle

function toggle(urldivID,csvdivID) {
  var x = document.getElementById(urldivID);
  var image=document.getElementById("urlorcsv");
  var title=document.getElementById("tab-header");
  if(x.style.display == "block"){
      x.style.display = "none";
      document.getElementById(csvdivID).style.display="block";
      image.src='/static/grader/images/Close.png';
      title.innerHTML="Upload CSV";

  }
  else{
      x.style.display = "block";
      document.getElementById(csvdivID).style.display="none";
      image.src= "/static/grader/images/Upload.png";
      title.innerHTML="URL";
      
  }
}
//Function to validate the urlfield 
//Returns false if empty
function validateForm() {
  document.getElementById('urlError').innerHTML=" "; //empty the error message when a new url is submitted
  var x = document.forms["studenturl"]["ref_url"].value;
  let regex = /https:\/\/[A-Za-z]+\.onshape\.com\/documents\/[A-Za-z0-9]+\/[A-Za-z]+\/[A-Za-z0-9]+\/e\/[A-Za-z0-9]+(?:\?|$)/i;
  if (!regex.test(x)){
    document.getElementById('urlError').innerHTML="Faulty urls detected. Please make sure the urls are correct." //show the error message
    document.forms["studenturl"]["ref_url"].value="";
    return false;   

      }

}


//Function to read contents of uploaded file - CSV file or Space separated file
function readfilecontent(){
  const fileInput = document.getElementById('csvfile');  //read file from the file upload button
  const selectedFile = fileInput.files[0];                // get the file
  let fr = new FileReader() ;                             //initiate FileReader class
  fr.readAsText(selectedFile)
  
  fr.onload = () => {
    parse_list_of_url(fr.result)
  }
  
  fr.onerror = () => {
    console.log(fr.error)
  }
}


//Function to read contents from the url field
function show_url_as_buttons(){
  let urllist = document.forms["urlform"]["url"].value; //get the value in the text field
  parse_list_of_url(urllist);
  document.forms["urlform"]["url"].value=""; //make text box empty
}

//Function to parse the list of url from the input form and display as closable buttons in list with id = urlButtonContainer

function parse_list_of_url(urllist){

  document.getElementById('urlError').innerHTML=" ";   //empty the error message when a new url is submitted
  var urlarray=urllist.split(/,\s*|\s+/);              //split the url based on space and commas
  uniqueUrls = [...new Set(urlarray)];                 //get the unique urls

  for (let i=0; i<uniqueUrls.length; i++){        //iterate over all the unique urls
    if(!uniqueUrls[i]== ""){                      //only if the url is not blank , might or might not need this
    //test urlvalidity 
      let regex = /https:\/\/[A-Za-z]+\.onshape\.com\/documents\/[A-Za-z0-9]+\/[A-Za-z]+\/[A-Za-z0-9]+\/e\/[A-Za-z0-9]+(?:\?|$)/i;
      if (regex.test(uniqueUrls[i])){
        addURLasbutton(uniqueUrls[i]);                        //add the valid onshape url as a button 
      }
      else{
        document.getElementById('urlError').innerHTML="At least one faulty url was detected. Please make sure all the urls are formatted correctly."
      }
    } 
  }
}


//Function to add url as a button inside the  list with id = urlButtonContainer  
function addURLasbutton(toadd){
  var listofurlbuttons = document.getElementById('urlButtonContainer');         //open the list 
  var urlbuttons_existing = listofurlbuttons.getElementsByTagName("li");        //get all the items in the list
  var urlarray_existing = Array.prototype.slice.call(urlbuttons_existing);        //convert the items into array
  
  //create array of just the ids of the url buttons - ids will be the full url - to make sure there is only one copy of each url
  var addedurls=[];   //create blank url array

  for (let i=0; i<urlarray_existing.length;i++){ 
    addedurls.push(urlarray_existing[i].id); 
  }


  //only create new button for urls that are not already in the button div (list)
  if(!addedurls.includes(toadd)){ 
    var newField = document.createElement('li'); //create an item is the list
    newField.setAttribute('id',toadd);            //set the url as the id
    newField.setAttribute('name',"ref_url[]");            //set the url as the id
    listofurlbuttons.appendChild(newField);       //create the list   
    item=document.getElementById(toadd);          //grab the new button for editing innerHTML    
    did= get_did_from_url(toadd);                 // grab the did from the url string 
    //add hyperlink 
    item.innerHTML= '<a href="'+ toadd + '"target="_blank">' + did +'</a>' + '<span class="close" onclick=removeUrl("'+toadd+'")>&times;</span>'; //update the content of the item with a closable icon and a js function on click
  }
checkURLs_for_enabling_grade_button(); //Function enables or disables the Grade model button - by checking for available URLs to grade 
}


// function to remove the button when clicked
function removeUrl(toremove){
  list=document.getElementById("urlButtonContainer"); //list the items in the list
  item=document.getElementById(toremove);             //find the item that needs to be removed
  list.removeChild(item);                           //remove from the selected item list
  checkURLs_for_enabling_grade_button();            //Function enables or disables the Grade model button - by checking for available URLs to grade 

}

//function to split the url into components
function get_did_from_url(url){
  ids=url.split('/');
  return (ids[2]+" "+ids[4]); //returning the onshape link and did
}



