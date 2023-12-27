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



function hide_all_divs(){
  console.log("I was called ");
  document.getElementById("part_studio_div").style.display = "none";
  document.getElementById("feature_div").style.display = "none";
  document.getElementById("parts_div").style.display = "none";
  document.getElementById("assembly_div").style.display = "none";
  document.getElementById("mates_div").style.display = "none";
  document.getElementById("instances_div").style.display = "none";
  console.log("I removed them");

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
    if(response.check_type[1]=="true"){ 
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
        document.getElementById("mate_count").innerHTML = response.mates_summary["summary_msg"]["mates"];                   // number of mates
        document.getElementById("mate_relations_count").innerHTML = response.mates_summary["summary_msg"]["mate_relations"]; // number of mate relations
        
      }
      else{
        //make mates studio div invisible
        document.getElementById("mates_div").style.display = "none"; 
      }
      if(response.check_type[1]=="true"){  
        //if Instances
        //make instances studio div visible
        document.getElementById("instances_div").style.display = "block";
        document.getElementById("instance_title").innerHTML = response.count_summary["title"];                             // title of list
        document.getElementById("instance_count").innerHTML = response.count_summary["instance_count"];                         // number of instances
        document.getElementById("part_instance_count").innerHTML = response.count_summary["part_instance_count"];           // number of instances that are parts
        document.getElementById("assemby_instance_count").innerHTML = response.count_summary["assemby_instance_count"];       // number of instances that are assemblies


      }
      else{
        //make instances studio div invisible
        document.getElementById("instances_div").style.display = "none"; 

      }



  }
    for (var key in response.count_summary) {
      console.log("key", key);
      console.log("value",response.count_summary[key]);
  }
    //console.log("what wil be  going on",Object.keys(response.count_summary))
    if(Object.keys(response.count_summary).length >0){
      console.log("part count is", response.count_summary["part_count"]);
      console.log("part material count is ", response.count_summary["part_material_count"]);
      console.log("part_renamecount is", response.count_summary["part_rename_count"]);
      console.log("surface", response.count_summary["part_surface_count"]);
    }

    if(response.features_details != {}){
      //console.log("called")
      for (var key in response.features_details["features"]) {
        //console.log("key", key);
        //console.log("value",response.features_details["features"][key]);
    }
      //console.log("error count is", response.features_details["error_count"]);
      //console.log("renamed feature count is ", response.features_details["renamed"]);

    }

    //console.log(response.mates_summary);
    //console.log(response.mate_details);
  }

  /*

  {
      #    "title": "Part Checking",  
      #    "part_count": part_count, 
      #    "part_rename_count": part_rename_count, 
      #    "part_material_count":part_material_count, 
      #    "part_surface_count": surface_count
      #   }
      #   For assemblies the summary contains  information about instances
      #  {
      #   "title":"Instance Checking", 
      #   "instance_count": instance_count, 
      #   "part_instance_count": part_instance_count, 
      #   "assemby_instance_count":assemby_instance_count
      #   }

      # features_details contains information about features in a part studio -
      #   {
      #   "features": features, 
      #   "renamed": renamed , 
      #   "error_count": error_count
      #   }
      #   features is a dict of {"feature name X ", number of times  feature X is used}
      #   renamed is an array of  [number_of_features, renamed_count]
      #   error_count is total number of errors in the features
      #
  {% if renamed %}
  <h3>Feature Checking</h3>
  <p>
  {% endif %}

  {% if summary_msg %}
  <h3>Mates Summary</h3> 
  <p class="list_title">This assembly contains:<ul class="summary">
  <li>Mates: {{ summary_msg.mates}}</li>
  <li>Mate relations: {{ summary_msg.mate_relations}}</li>
  </ul>
  </p>

  {% endif %}

  part_message = f'''
  <h3>Part Checking</h3>
  <p>There is/are {part_count} part(s) in this part studio. <br>
  {part_rename_count}/{part_count} parts are renamed. <br>
  {part_material_count}/{part_count} parts have a material assigned.</p>
  '''

  if surface_count > 0:
      part_message += f'''
      <p>There are {surface_count} surfaces in this part studio.</p>
      '''


      part_message = f'''
      <h3>Instance Checking</h3>
      <p>There are {instance_count} instances in this assembly, with {part_instance_count} parts and {assemby_instance_count} sub-assemblies inserted.</p>
      '''
      
      feature_message = f'''
      <h3>Feature Checking</h3>
      <p>This assembly has {mate_count} mates and {mate_relation_count} mate relations.</p>
      '''
  {% if check_message %}
  {{ check_message|safe }}
  {% endif %}

  {% if renamed %}
  <h3>Feature Checking</h3>
  <p>This part studio has {{ renamed.0 }} features (not including Origin and default planes).<br>
      Of those features, {{ renamed.1 }} have been renamed.</p>
  {% endif %}

  {% if ps_error_count %}
  <p>Total number of errors: {{ps_error_count}}</p>
  {% endif %}

  {% if features %}
  <p class="table_title">Feature Count</p>
  <table class="item_summary">
      <thead><tr><th>Type</th><th>Count</th></tr></thead>
      <tbody>
      {% for key, value in features.items %}
          <tr>
              <td>{{ key }}</td>
              <td>{{ value }}</td>
              </tr>
      {% endfor %}
      </tbody>
  </table>
  {% endif %}
  */