
/*AJAX Function to build User properties table*/
function build_user(response){
    var user_props = response.user_props;
    var reference_table = document.getElementById("reference"); //open the reference table 
    var user_data_loaded = document.getElementById("user_data_loaded");
    if(user_data_loaded.value == "false"){
      user_data_loaded.value = "true"; //to make sure to update the table only once
      document.getElementById("usr_docname").innerHTML = user_props[0][0];
      document.getElementById("usr_username").innerHTML = user_props[0][1];
      document.getElementById("usr_url").innerHTML = user_props[0][5];

      if (response.etype == 'partstudios'){ //if the etype is part studios then add a column called part name for parts
        col0 =  document.createElement("col");
        col0.classList.add("col_0");
        reference_table.insertBefore(col0, reference_table.firstChild)

        var header_row = document.getElementById("user_table_header");
        var col0_header = header_row.insertCell(0);
        col0_header.outerHTML = "<th>Part Name</th>";
      }

      for (let index = 1; index < user_props.length; index++){
        var hidden_row = document.createElement("tr"); //create a new row
        var row = document.createElement("tr"); //create a new row
        // Create cells
        let c0 = document.createElement("td");
        let c1 = document.createElement("td");
        let c2 = document.createElement("td");
        let c3 = document.createElement("td");
        let c4 = document.createElement("td");
        let c0h = document.createElement("td");
        let c1h = document.createElement("td");
        let c2h = document.createElement("td");
        let c3h = document.createElement("td");
        let c4h = document.createElement("td");
        
        if (response.etype == 'partstudios'){

                //create a cell for part name (td)
                c0.setAttribute('id','usr_0_'+ index);
                c0h.setAttribute('id','husr_0_'+ index);

                //create a div for tooltip
                let tooltip = document.createElement("div");
                tooltip.setAttribute('class','tooltip centered');
                tooltip.setAttribute('value',user_props[index][4][0]);
                tooltip.innerText = user_props[index][4][0];

                //create a span for tooltip text
                let tooltiptext = document.createElement("span");
                tooltiptext.setAttribute('id','usr_0_span'+ index);
                tooltiptext.setAttribute('class','tooltiptext tooltiptext_top');
                tooltiptext.innerHTML = user_props[index][4][1];

                //append the tooltiptext to tooltip div
                tooltip.appendChild(tooltiptext);

                //append the tooltip div to td
                c0.appendChild(tooltip);

                //append the td to row
                row.appendChild(c0);
                hidden_row.appendChild(c0h);
              }

        c1.setAttribute('id','usr_1_'+ index);
        c1.innerText = user_props[index][0];
        row.appendChild(c1);
        c1h.setAttribute('id','husr_1_'+ index);
        c1h.innerText = user_props[index][0];
        hidden_row.appendChild(c1h);

        c2.setAttribute('id','usr_2_'+ index);
        c2.innerText = user_props[index][1];
        row.appendChild(c2);
        c2h.setAttribute('id','husr_2_'+ index);
        c2h.innerText = user_props[index][1];
        hidden_row.appendChild(c2h);

        c3.setAttribute('id','usr_3_'+ index);
        c3.innerText = user_props[index][2];
        row.appendChild(c3);
        c3h.setAttribute('id','husr_3_'+ index);
        c3h.innerText = user_props[index][2];
        hidden_row.appendChild(c3h);

        c4.setAttribute('id','usr_4_'+ index);
        c4.innerText = user_props[index][3];
        row.appendChild(c4);
        c4h.setAttribute('id','husr_4_'+ index);
        c4h.innerText = user_props[index][3];
        hidden_row.appendChild(c4h);

        // Append row to table body
        reference_table.appendChild(row);
        hidden_row.style.display = 'none'
        reference_table.appendChild(hidden_row);
      }
    }
    round_off_reference_table(user_props.length);
  }

/*AJAX Function to build results properties tables*/
function build_results(response, url_num){
  var ref_props = response.ref_props;
  var results_table = document.getElementById("table_" + url_num); //open the results table 
  if(response.failed_url == "None"){
    document.getElementById("ref_docname_"+ url_num).innerHTML = ref_props[0][0];
    document.getElementById("ref_username_"+ url_num).innerHTML = ref_props[0][1];
    document.getElementById("name_" + url_num).innerHTML = ref_props[0][2]; 
    document.getElementById("elname_" + url_num).innerHTML = ref_props[0][2];
    document.getElementById("thumbnail_" + url_num).src = ref_props[0][4];
    document.getElementById("name_" + url_num).href = ref_props[0][5];
    document.getElementById("url_" + url_num).innerHTML = ref_props[0][5];
    if (response.etype == 'partstudios'){ //if the etype is part studios then add a column called part name for parts
      col0 =  document.createElement("col");
      col0.classList.add("col_0");
      results_table.insertBefore(col0, results_table.firstChild)

      var header_row = document.getElementById("ref_table_header_" + url_num);
      var col0_header = header_row.insertCell(0);
      col0_header.outerHTML = "<th>Part Name</th>";
    }
    for (let index = 1; index < ref_props.length; index++){
      var row = document.createElement("tr"); //create a new row
      var hidden_row = document.createElement("tr"); //create a new row
      // Create cells
      let c0 = document.createElement("td");
      let c1 = document.createElement("td");
      let c2 = document.createElement("td");
      let c3 = document.createElement("td");
      let c4 = document.createElement("td");
      let c0h = document.createElement("td");
      let c1h = document.createElement("td");
      let c2h = document.createElement("td");
      let c3h = document.createElement("td");
      let c4h = document.createElement("td");
      if (response.etype == 'partstudios'){

                  //create a cell for part name (td)
                  c0.setAttribute('id', 'ref_0_'+ url_num + '_' + index);
                  c0h.setAttribute('id','href_0_'+ url_num + '_' + index);

                  //create a div for tooltip
                  let tooltip = document.createElement("div");
                  tooltip.setAttribute('value',ref_props[index][4][0]);
                  tooltip.setAttribute('class','tooltip centered');
                  tooltip.innerText = ref_props[index][4][0];
        
                  //create a span for tooltip text
                  let tooltiptext = document.createElement("span");
                  tooltiptext.setAttribute('id', 'ref_0_span'+ url_num + '_' + index);
                  tooltiptext.setAttribute('class','tooltiptext tooltiptext_top');

                  //add tooltip text
                  tooltiptext.innerHTML = ref_props[index][4][1];
        
                  //append the tooltiptext to tooltip div
                  tooltip.appendChild(tooltiptext);
        
                  //append the tooltip div to td
                  c0.appendChild(tooltip);
        
                  //append the td to row
                  row.appendChild(c0);
                  hidden_row.appendChild(c0h);
      }

      c1.setAttribute('id','ref_1_'+ url_num + '_' + index);
      c1.innerText = ref_props[index][0];
      row.appendChild(c1);
      c1h.setAttribute('id','href_1_'+ url_num + '_' + index);
      c1h.innerText = ref_props[index][0];
      hidden_row.appendChild(c1h);

      c2.setAttribute('id','ref_2_'+ url_num + '_' + index);
      c2.innerText = ref_props[index][1];
      row.appendChild(c2);
      c2h.setAttribute('id','href_2_'+ url_num + '_' + index);
      c2h.innerText = ref_props[index][1];
      hidden_row.appendChild(c2h);

      c3.setAttribute('id','ref_3_'+ url_num + '_' + index);
      c3.innerText = ref_props[index][2];
      row.appendChild(c3);
      c3h.setAttribute('id','href_3_'+ url_num + '_' + index);
      c3h.innerText = ref_props[index][2];
      hidden_row.appendChild(c3h);

      c4.setAttribute('id','ref_4_'+ url_num + '_' + index);
      c4.innerText = ref_props[index][3];
      row.appendChild(c4);
      c4h.setAttribute('id','href_4_'+ url_num + '_' + index);
      c4h.innerText = ref_props[index][3];
      hidden_row.appendChild(c4h);

      // Append row to table body
      results_table.appendChild(row);
      hidden_row.style.display = 'none'
      results_table.appendChild(hidden_row);
    }
    
    round_off_results_table(url_num);
    calculate_error_for_url(url_num);
  }
  else{
    //hide the box for failed results
    document.getElementById("property_box_" + url_num).style.display = 'none';
    //show the failed results container box
    document.getElementById("failed_url_box").style.display = "block";
    //get the failed url list
    var failed_url_list = document.getElementById("failed_url_list");
    //creat a new entry to failed url list
    var new_url = document.createElement("li");
    //set error message for title - get more info on hover
    new_url.setAttribute('title', response.error_msg);
    new_url.innerHTML = "<a href = " + response.failed_url + " target = '_blank'>" + response.failed_url + "</a>";
    failed_url_list.appendChild(new_url);

  }
}


/*
This function rounds off the data fromt the table to 6 decimal places
!! FUTURE WORK : round the floating points based on the user's desired rounding scheme !! 

Arguments :   num_of_urls
  - num_of_urls is the total number of urls that successfully returned properties (i.e. number of cards (tables) in the results page)
*/


function reform_result(num_of_urls){

  //checking the list of properties user wants to compare
  var checkboxstatus = [];
  for( let i = 1; i< 5 ; i++){
    checkboxstatus[i] = document.getElementById("check_"+ i).checked;
  }
  for (let url = 0 ; url <= num_of_urls ; url++ ){
    for( let i = 1; i < 5 ; i++){
      if(!checkboxstatus[i]){
        document.getElementsByClassName('col_' + i)[url].style.visibility='collapse';
      }
      else{
      document.getElementsByClassName('col_' + i)[url].style.visibility='visible';
      }
    }
  }
  compute_error(num_of_urls);
}


function round_off_reference_table(num_of_parts){
  var precision_input = document.getElementById("precision_input");
  var precison = Number(precision_input.value - 1) ; //set the precison 
  for (let part = 1; part < num_of_parts; part++){
    //round off data for each part in the user document 
    for (let p = 1; p < 5; p++){
      var data = document.getElementById("husr_" + p + "_" + part).innerHTML;
      if(9 < data || data < 1){
        document.getElementById("usr_" + p + "_" + part).innerHTML = Number(data).toExponential(precison);
      }
      else{
        document.getElementById("usr_" + p + "_" + part).innerHTML = Number(data).toFixed(precison);
      }
    }
  }
}

function round_off_results_table(url_num, precison = 3){
  var precision_input = document.getElementById("precision_input");
  var precison = Number(precision_input.value - 1) ; //set the precison 
  //find url data from table using table id . table id are autogenerated with format "table_[count]" 
  var ref_table = document.getElementById("table_" + url_num); 
  var ref_number_of_parts = ref_table.getElementsByTagName("tr").length/2;
  //for each part 
  for (let part = 1; part < ref_number_of_parts; part++){
    //for each column
    for (let p = 1; p < 5; p++){
      var data = document.getElementById("href_" + p + "_" + url_num + "_" + part).innerHTML;
      if(9 < data || data < 1){
        document.getElementById("ref_" + p + "_" + url_num + "_" + part).innerHTML = Number(data).toExponential(precison);
      }
      else{
        document.getElementById("ref_" + p + "_" + url_num + "_" + part).innerHTML = Number(data).toFixed(precison);
      }
    }
  }

}

function re_round_tables(num_of_urls){
  var ref_table = document.getElementById("reference"); 
  var ref_number_of_parts = ref_table.getElementsByTagName("tr").length/2;
  round_off_reference_table(ref_number_of_parts)
  for (let url = 0; url < num_of_urls; url++ ){ //for property in each url 
    //find url data from table using table id . table id are autogenerated with format "table_[count]" 
    round_off_results_table(url);
  }
}


function compute_error(num_of_urls){

  for (let url = 0; url < num_of_urls; url++ ){ //for property in each url 
      //find url data from table using table id . table id are autogenerated with format "table_[count]" 
      calculate_error_for_url(url);
  }
}
   

function calculate_error_for_url(url){
  /*
  This function calculates errors and hence the score or grade for each url inputted by the user as comapred with the property of model the app is currently opened on
  Error percentages are calculated with formula (user-reference)/reference * 100 

  Arguments :  url 
    - url is the number (index) of the url that is to be calculated
  */

  //checking the list of properties user wants to compare
  checkboxstatus = []; //blank array to store check box info
  for( let i = 1; i< 5 ; i++){
    checkboxstatus[i] = document.getElementById("check_"+ i).checked;
  }


  //grab reference data from reference table
  var usr_table = document.getElementById("reference");
  var usr_number_of_parts = usr_table.getElementsByTagName("tr").length/2; //number of parts 


  //grab  user selected acceptable error rate
  var slider = document.getElementById("tolerance_slider");
  document.getElementById('slider_value').innerHTML=slider.value;
  error=Number(slider.value);

  var ref_table = document.getElementById("table_" + url); 
    var ref_number_of_parts = ref_table.getElementsByTagName("tr").length/2; //number of parts

    var score = 0;
    for (let part = 1; part < Math.min(usr_number_of_parts, ref_number_of_parts) ; part++){
      //get material data for user doc
      if (document.getElementById("usr_0_" + part)){
        user_material = document.getElementById("usr_0_span" + part).innerHTML;
        ref_material = document.getElementById("ref_0_span" + url + "_" + part).innerHTML;

        if(user_material == ref_material){
          document.getElementById("ref_0_" + url + "_" + part).style.border = "1px solid #009400";
        }
        else{
          document.getElementById("ref_0_" + url + "_" + part).style.border = "1px solid #BD3039";
        }
      }

    //calculate error

      for (let p = 1; p < 5; p++){
        //get data for usr doc
        var usrdata = document.getElementById("usr_" + p + "_" + part).innerHTML;
          //get data for url docs
        var refdata = document.getElementById("ref_" + p + "_" + url + "_" + part).innerHTML;
        //calculate error
        var errdata = Math.abs(refdata - usrdata) * 100 / usrdata;
        
        if(checkboxstatus[p]){ //calculate error only if the correspnding checkbox is clicked
          if (errdata > error){
            document.getElementById("ref_" + p + "_" + url + "_" + part).className = "red";
            score = score + 1;    
          }
          else{
            document.getElementById("ref_" + p + "_" + url + "_" + part).className = "green";
          }
        }   
      }
    }

    if(score > 0){
      document.getElementById("ref_score_"+ url).innerHTML = "<img src=\"/static/grader/images/red-x.png\" width='14px'>";
    }
    else{
      document.getElementById("ref_score_"+ url).innerHTML = "<img src=\"/static/grader/images/green-check.svg\" width='18px'>";
    }

    
    if(usr_number_of_parts != ref_number_of_parts){
        var text=document.getElementById("error_message_" + url);
        if(usr_number_of_parts > ref_number_of_parts){
          text.innerHTML="Some parts are missing.";
        }
        else {
          text.innerHTML="Extra parts were detected.";
        }
        ref_table.style.display="none";
        document.getElementById("ref_score_"+ url).innerHTML =  "<img src=\"/static/grader/images/red-x.png\" width='14px'>";
    }
  }

  //Function to show pop up
  function show_popup(popup){
    var reasons = document.getElementById(popup);
    reasons.style.display = "block"; 
  }

  //Function to  hide pop up
  function hide_popup(popup){
    var reasons = document.getElementById(popup);
    reasons.style.display = "none";
  }
   
