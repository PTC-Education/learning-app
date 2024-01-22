function tableToCSV(num_of_urls) {

	var csv_data = [];
	var refTable = document.getElementById('reference');
	var column_info = refTable.querySelectorAll('col');

// ******************* /
	//Header start
	csvrow = [];
	csvrow.push("Owner", "Comment", "Document", "Doc Time");

	if(column_info[0].className == "col_0") { // if Part Name column exists
		csvrow.push("Tab Name");
	}
	csvrow.push("Mass/Center of Mass","Tab Points","Total Points","URL"); //rest of headers
	csv_data.push(csvrow.join(",")); //First row with headers

	//Header end
	//******************* */

	//Document owner information of the user
	csvrow = [];
	var docname = document.getElementById("usr_docname").innerHTML;
	var username = document.getElementById("usr_username").innerHTML;
	var userurl = document.getElementById("usr_url").innerHTML;
    var userscore = document.getElementById("usr_score").innerHTML;
    var doctime = document.getElementById("usr_doctime").innerHTML;
	csvrow.push(username,"Answer Key", docname, doctime, "", "", "", userscore, userurl); //element name and score are left blank
	csv_data.push(csvrow.join(",")); //Next row with document information 
	
	//Document property information of the user
	var all_parts = refTable.querySelectorAll('tr');
	for (let r = 1; r < all_parts.length ; r++){ //excluding the first row
		csvrow = ["","","",""]; //first four blank cells 
		var part = all_parts[r].querySelectorAll('td'); // grab the part information within all parts
		for (let i = 0; i < part.length ; i++){
            if (part[i].innerHTML.includes(",")){ // if the part is an assembly, COM is outputted in 3 cols
				com = part[i].innerHTML
				strcom = ""
				res = strcom.concat("\"", com, "\"")
				console.log("res:", res)
                csvrow.push(res);
            }
            else{
				csvrow.push(part[i].innerHTML); 
            }
		}
		csv_data.push(csvrow.join(",")); //Next row with properties
	}

	//Document name and owner information of the document from the urls
	for (let u = 0; u< num_of_urls; u++){
		csvrow = [];
		var docname = document.getElementById("ref_docname_" + u).innerHTML;
		var username = document.getElementById("ref_username_" + u).innerHTML;
		var docscore = document.getElementById("ref_docscore_" + u).innerHTML;
        var doctime = document.getElementById("ref_doctime_" + u).innerHTML;
		var url =   document.getElementById('url_' + u).innerHTML;
		var error_message = document.getElementById("error_message_" + u).innerHTML;
	
		csvrow.push(username, error_message, docname, doctime, "", "", "", docscore, url); 
		csv_data.push(csvrow.join(",")); //Next row with document information 

		if(error_message == ""){ //Ignore the data if there is any  error message
			var refTable = document.getElementById('table_' + u);
			var all_parts = refTable.querySelectorAll('tr');
			for (let r = 1; r < all_parts.length ; r++){ //excluding the first row
				csvrow = ["","","",""]; //blank row
				var part = all_parts[r].querySelectorAll('td'); // grab the part information within all parts
				for (let i = 0; i < part.length ; i++){
					if(column_info[0].clasName == "col_0") { 
						csvrow.push(part[0].innerHTML);  // add part name to the list if part name column exist
					}
					else if(column_info[i].style.visibility == "collapse"){ //add blank cell to the collapsed column
						csvrow.push(""); 
					}
					else if(column_info[i].style.visibility != "collapse"){
						if (part[i].innerHTML.includes(",")){ // if the part is an assembly, COM is outputted in 3 cols
							console.log("if triggered");
							com = part[i].innerHTML
							strcom = ""
							res = strcom.concat("\"", com, "\"")
							console.log("res:", res)
							csvrow.push(res);
						}
						else{
							console.log("else triggered");
							csvrow.push(part[i].innerHTML); 
						}
					}
				}
			csv_data.push(csvrow.join(",")); //Next row with properties
			}
		}
	}

	//Adding failed URLs to the report
	
	var urllist = document.getElementById('failed_url_list');
	if(urllist != null){
		var failedurls = urllist.querySelectorAll('a');
		//console.log(failedurls); //add to the report 
		for(let i = 0; i < failedurls.length; i++){
			csvrow = [];
			csvrow.push("", "!" , "Failed URL", "", "",  failedurls[i].innerHTML);
			csv_data.push(csvrow.join(","));
		}
	}

	//for failed URLS

	csv_data=csv_data.join("\n");
    downloadCSVFile(csv_data);
}

function downloadCSVFile(csv_data) {
 
    // Create CSV file object and feed our
    // csv_data into it
    CSVFile = new Blob([csv_data], { type: "text/csv" });
 
    // Create to temporary link to initiate
    // download process
    var temp_link = document.createElement('a');
 
    // Download csv file
    temp_link.download = "Report.csv";
    var url = window.URL.createObjectURL(CSVFile);
    temp_link.href = url;
 
    // This link should not be displayed
    temp_link.style.display = "none";
    document.body.appendChild(temp_link);
 
    // Automatically click the link to trigger download
    temp_link.click();
    document.body.removeChild(temp_link);
}