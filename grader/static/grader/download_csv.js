
//TO FIX : make the final csv downloadable and rightly formatted

function tableToCSV(num_of_parts, num_of_urls) {

	var csv_data = [];
	var refTable = document.getElementById('reference');
	var column_info = refTable.querySelectorAll('col');


// ******************* /
	//Header start
	csvrow = [];
	csvrow.push("Document Name", "Document Owner","Element Name","Score","Comment");

	if(column_info[0].className == "col_0") { // if Part Name column exists
		csvrow.push("Part Name");
	}
	csvrow.push("Mass","Volume","Surface Area","Principal MOI","URL");
	csv_data.push(csvrow.join(",")); //First row with headers

	//Header end
	//******************* */


	//Document name and owner information of the user
	var csvrow = [];
	var docname = document.getElementById("usr_docname").innerHTML;
	var username = document.getElementById("usr_username").innerHTML;
	csvrow.push(docname, username,"","", "Reference Document"); //element name and score are left blank
	csv_data.push(csvrow.join(",")); //Next row with document information 
	
	var all_parts = refTable.querySelectorAll('tr');
	for (let r = 1; r < all_parts.length ; r++){ //excluding the first row
		csvrow = ["","","","",""]; //blank row
		var part = all_parts[r].querySelectorAll('td'); // grab the part information within all parts
		for (let i = 0; i < part.length ; i++){
			if(column_info[0].clasName == "col_0") { 
				csvrow.push(part[0].innerHTML);  // add part name to the list if part name column exist
			}
			else if(column_info[i].style.visibility != "collapse"){
				csvrow.push(part[i].innerHTML); 
			}
		}
		csv_data.push(csvrow.join(",")); //Next row with properties
		
	}



	//Document name and owner information of the document from the urls
	for (let u = 0; u< num_of_urls; u++){
		var csvrow = [];
		var docname = document.getElementById("ref_docname_" + u).innerHTML;
		var username = document.getElementById("ref_username_" + u).innerHTML;
		var elname =   document.getElementById('elname_' + u).innerHTML;
		var score = document.getElementById("ref_score_" + u).innerHTML;
		var url =   document.getElementById('url_' + u).innerHTML;
		var mismatcherror = document.getElementById("error_message_" + u).innerHTML;
	
		csvrow.push(docname, username, elname , score, mismatcherror,url); 
		csv_data.push(csvrow.join(",")); //Next row with document information 
		if(mismatcherror == ""){ //Ignore the data if there is any mismatch error
			var refTable = document.getElementById('table_' + u);
			var all_parts = refTable.querySelectorAll('tr');
			for (let r = 1; r < all_parts.length ; r++){ //excluding the first row
				csvrow = ["","","","",""]; //blank row
				var part = all_parts[r].querySelectorAll('td'); // grab the part information within all parts
				for (let i = 0; i < part.length ; i++){
					if(column_info[0].clasName == "col_0") { 
						csvrow.push(part[0].innerHTML);  // add part name to the list if part name column exist
					}
					else if(column_info[i].style.visibility != "collapse"){
						csvrow.push(part[i].innerHTML); 
					}
				}
			csv_data.push(csvrow.join(",")); //Next row with properties
			}
		}
	}
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