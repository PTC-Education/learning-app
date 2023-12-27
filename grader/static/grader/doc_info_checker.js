function showHideDetails(d,div)
{
   if(d.checked == true )
      document.getElementById(div).style.display = "block";
   else
      document.getElementById(div).style.display = "none";
}
function hide()
{
    document.getElementById('mates_details').style.display = "none";
}
function selectRadio(selectedDiv) {
    // Deselect all divs
    const radios = document.querySelectorAll('.single-radio');
    radios.forEach(div => div.classList.remove('selected'));
    // Select the clicked div
    selectedDiv.classList.add('selected');
    const selectedRadio = document.querySelector('.single-radio.selected');
    if (selectedRadio) {
        const selectedValue = selectedRadio.getAttribute('data-value');
        document.getElementById("elements").value = selectedValue;
        change_check_box_text(selectedValue.split(" ")[0]);
    }
}

function change_check_box_text(etype){
  if(etype == 'partstudios'){
    document.getElementById("Fcheck").innerHTML = "Features";
    document.getElementById("Pcheck").innerHTML = "Parts";
  }
  else if (etype == 'assemblies'){
    document.getElementById("Fcheck").innerHTML = "Mates";
    document.getElementById("Pcheck").innerHTML = "Instances";

  }
}
function formSubmit() {
    const selectedRadio = document.querySelector('.single-radio.selected');
    if (selectedRadio) {
        document.getElementById("msg").innerHTML = "";
        loading_spinner('features')
    } else {
        document.getElementById("msg").innerHTML = "Please select an element.";
        return false;
    }
    return true;
}

function is_proper_selection_made(check_type, elements){
  return ((check_type[0] || check_type[1]) && elements.indexOf(' ') >= 0)
}

function hide_all_divs(){
  document.getElementById("part_studio_div").style.display = "none";
  document.getElementById("feature_div").style.display = "none";
  document.getElementById("parts_div").style.display = "none";
  document.getElementById("assembly_div").style.display = "none";
  document.getElementById("mates_div").style.display = "none";
  document.getElementById("instances_div").style.display = "none";
}

function build_page(response){
  //hide all the existing divs
  hide_all_divs();

  //Check if it is a part studio it is a part studio or an assembly
  if (response.etype == "partstudios"){
    //make part studio div visible
    document.getElementById("part_studio_div").style.display = "block";                                
    
    //check which button is checked
    if(response.check_type[0] =="true"){    
      //if  Features    
      //make feature div visible                                                       
      document.getElementById("feature_div").style.display = "block";                                  
      document.getElementById("renamed0").innerHTML = response.features_details["renamed"][0];          // number of total features
      document.getElementById("renamed1").innerHTML = response.features_details["renamed"][1];          // number of renamed features
      document.getElementById("ps_errors").innerHTML = response.features_details["error_count"];         // number of errors in features

      //GENERATING FEATURE TABLE
      var features_table =  document.getElementById("features_details_table")
      
      //to avoid appending to the same table
      //delete existing tbody
      var old_tbody = features_table.getElementsByTagName("tbody")[0];
      features_table.removeChild(old_tbody);
 
      //create new tbody
      var tbody = document.createElement("tbody");
      for (var key in response.features_details["features"]) {
        var row = document.createElement("tr"); //create a new row
        let c0 = document.createElement("td");
        let c1 = document.createElement("td");
        c0.innerText = key;
        c1.innerText = response.features_details["features"][key];
        row.appendChild(c0);
        row.appendChild(c1);
        tbody.appendChild(row);
      }   
      features_table.appendChild(tbody);  
      
    }
    else{
      //make feature div invisible
      document.getElementById("feature_div").style.display = "none";                                    
    }


    if(response.check_type[1] == "true"){ 
      //if Parts
      //make parts  div visible                                                               
      document.getElementById("parts_div").style.display = "block";  

      document.getElementById("parts_title").innerHTML = response.count_summary["title"];               // title of list
      document.getElementById("part_count").innerHTML = response.count_summary["part_count"];          // number of parts
      document.getElementById("part_rename_count").innerHTML = response.count_summary["part_rename_count"];          // number of renamed parts
      document.getElementById("part_material_count").innerHTML = response.count_summary["part_material_count"];         // number of parts with materials
      document.getElementById("part_surface_count").innerHTML = response.count_summary["part_surface_count"];         // number of surfaces
    }
    else{
      //make parts  div invisible
      document.getElementById("parts_div").style.display = "none";                                     
    }

  }

  else if(response.etype == "assemblies"){
      //make assembly div visible
      document.getElementById("assembly_div").style.display = "block";    

      if(response.check_type[0]=="true"){    
        //if  Mates 
        //make mates studio div visible                                                            
        document.getElementById("mates_div").style.display = "block";   
        
        //mate and mate_relation details
        var number_of_mates = response.mates_summary["summary_msg"]["mates"];  
        var number_of_mate_relations = response.mates_summary["summary_msg"]["mate_relations"];
        document.getElementById("mate_count").innerHTML = number_of_mates;                                                  // number of mates
        document.getElementById("mate_relations_count").innerHTML = number_of_mate_relations;                                // number of mate relations
        document.getElementById("error_count").innerHTML = response.mates_summary["error_count"];                             // number of errors in mates
        
        document.getElementById("renamed").innerHTML = response.mate_details["detail_msg"]["renamed"];                         // number of instances
        document.getElementById("offsets").innerHTML = response.mate_details["detail_msg"]["offsets"];           // number of instances that are parts
        document.getElementById("limits").innerHTML = response.mate_details["detail_msg"]["limits"];       // number of instances that are assemblies
     
        var  mates_table_div =  document.getElementById("mates_table_div");

        if(number_of_mates > 0){
          mates_table_div.style.display = "block";

          //GENERATING MATES TABLE
          var  mates_table =  document.getElementById("mates_table");
          
          //to avoid appending to the same table
          //delete existing tbody
          var old_tbody = mates_table.getElementsByTagName("tbody")[0];
          mates_table.removeChild(old_tbody);
    
          //create new tbody
          var tbody = document.createElement("tbody");
          for (var key in response.mates_summary["mates"]) {
            var row = document.createElement("tr"); //create a new row
            let c0 = document.createElement("td");
            let c1 = document.createElement("td");
            c0.innerText = key;
            c1.innerText = response.mates_summary["mates"][key];
            row.appendChild(c0);
            row.appendChild(c1);
            tbody.appendChild(row);
          }   
          mates_table.appendChild(tbody);  
        }
        else{
          mates_table_div.style.display = "none";
        }

        var  mate_relations_table_div =  document.getElementById("mate_relations_table_div");
        if(number_of_mate_relations > 0){
          mate_relations_table_div.style.display = "block";

          //GENERATING MATE RELATIONS TABLE
          var  mate_relations_table =  document.getElementById("mate_relations_table");
          //to avoid appending to the same table
          //delete existing tbody
          var old_tbody = mate_relations_table.getElementsByTagName("tbody")[0];
          mate_relations_table.removeChild(old_tbody);
    
          //create new tbody
          var tbody = document.createElement("tbody");
          for (var key in response.mates_summary["mate_relations"]) {
            var row = document.createElement("tr"); //create a new row
            let c0 = document.createElement("td");
            let c1 = document.createElement("td");
            c0.innerText = key;
            c1.innerText = response.mates_summary["mate_relations"][key];
            row.appendChild(c0);
            row.appendChild(c1);
            tbody.appendChild(row);
          }   
          mate_relations_table.appendChild(tbody); 
        }
        else{
          mate_relations_table_div.style.display = "none";
        }

        
        var  mates_details_div =  document.getElementById("mates_details_div"); //div containing the table
        if(number_of_mates > 0 || number_of_mate_relations > 0){

          mates_details_div.style.display = "block";

          //GENERATING MATE DETAILS TABLE
          var  mate_details_table =  document.getElementById("mate_details_table");
          
          //to avoid appending to the same table
          //delete existing tbody
          var old_tbody = mate_details_table.getElementsByTagName("tbody")[0];
          mate_details_table.removeChild(old_tbody);
    
          //create new tbody
          var tbody = document.createElement("tbody");

          for (let i = 0; i< response.mate_details["mate_details"].length ; i++){
            var row = document.createElement("tr"); //create a new row
            let c0 = document.createElement("td"); //name
            let c1 = document.createElement("td"); //Type
            let c2 = document.createElement("td"); //Limits
            let c3 = document.createElement("td"); //Offsets
            let c4 = document.createElement("td"); //renamed (boolean)

            c0.innerText = response.mate_details["mate_details"][i]["name"];
            c1.innerText = response.mate_details["mate_details"][i]["type"];
            
            if(response.mate_details["mate_details"][i].hasOwnProperty('limits')){
              var limits = response.mate_details["mate_details"][i]["limits"];
                var limit_html = "";
                for(let j =0; j < limits.length ; j++){
                  limit_html += limits[j][0] + " : " + limits[j][1] + "\n";
                }
                c2.innerText = limit_html;
            }

            if(response.mate_details["mate_details"][i].hasOwnProperty('offsets')){
              var offsets = response.mate_details["mate_details"][i]["offsets"];
                var offsets_html = "";
                for(let j =0; j < offsets.length ; j++){
                  offsets_html += offsets[j][0] + " : " + offsets[j][1] + "\n";
                }
                c3.innerText = offsets_html;
            }
            
            if (response.mate_details["mate_details"][i]["renamed"] == "true"){
              c4.innerText = "✓";
            }
            else{
              c4.innerText = "✗";
            }

          row.appendChild(c0);
          row.appendChild(c1);
          row.appendChild(c2);
          row.appendChild(c3);
          row.appendChild(c4);
          tbody.appendChild(row);
          }   
          mate_details_table.appendChild(tbody); 
        }
        else{
          //make mates details table div invisible
          mates_details_div.style.display = "none";
        }
      }
      else{
        //make mates studio div invisible
        document.getElementById("mates_div").style.display = "none";  
      }
      if(response.check_type[1]=="true"){  
        //if Instances
        //make instances studio div visible
        document.getElementById("instances_div").style.display = "block";
        document.getElementById("instance_title").innerHTML = response.count_summary["title"];                              // title of list
        document.getElementById("instance_count").innerHTML = response.count_summary["instance_count"];                     // number of instances
        document.getElementById("part_instance_count").innerHTML = response.count_summary["part_instance_count"];           // number of instances that are parts
        document.getElementById("assemby_instance_count").innerHTML = response.count_summary["assemby_instance_count"];     // number of instances that are assemblies
      }
      else{
        //make instances studio div invisible
        document.getElementById("instances_div").style.display = "none"; 
      }
    }
  }