function tableToCSV(num_of_urls) {
	var csv_data = [];
	var refTable = document.getElementById('reference');
	var column_info = refTable.querySelectorAll('col');

	// First Row
	let csvrow = [];
	csvrow.push("Document Owner", "Pass/Fail", "Document Name", "Element Name");

	if(column_info[0].className == "col_0") { // if Part Name column exists
		csvrow.push("Part Name");
		csvrow.push("Material");
	}
	csvrow.push("Mass", "Volume", "Surface Area", "Principal MOI", "URL"); //rest of headers
	csv_data.push(csvrow.join(",")); //First row with headers

	// Ref Document
	csvrow = [];
	var docname = document.getElementById("usr_docname").innerHTML;
	var username = document.getElementById("usr_username").innerHTML;
	var userurl = document.getElementById("usr_url").innerHTML;

	csvrow.push(docname, "", username, ""); //element name and score are left blank

	var all_parts = refTable.querySelectorAll('tr');
	for (let r = 1; r < all_parts.length ; r++){ //excluding the first row
		if (r % 2 !== 0) {
			var part = all_parts[r].querySelectorAll('td'); // grab the part information within all parts
			for (let i = 0; i < part.length ; i++){
				if(column_info[i].className == "col_0") { 
					csvrow.push(part[i].querySelectorAll('div')[0].getAttribute('value')); // add part name to the list if part name column exist
					csvrow.push(part[i].querySelectorAll('span')[0].innerHTML); // add material name to the list if part name column exist
				}
				else if(column_info[i].style.visibility == "collapse"){ //add blank cell to the collapsed column
					csvrow.push(""); 
				}
				else if(column_info[i].style.visibility != "collapse"){
					csvrow.push(part[i].innerHTML);
				}
				
			}
		}
	}

	// Add URL
	csvrow.push(userurl);
	csv_data.push(csvrow.join(","));

	// Graded docs
	for (let u = 0; u< num_of_urls; u++){
		csvrow = [];
		var docname = document.getElementById("ref_docname_" + u).innerHTML;
		var username = document.getElementById("ref_username_" + u).innerHTML;
		var elname =   document.getElementById('elname_' + u).innerHTML;
		var score;
		if (document.getElementById("ref_score_" + u).innerHTML.includes('red-x')) {
			score = "Fail";
		} else {
			score = "Pass";
		}
		var url =   document.getElementById('url_' + u).innerHTML;
		var error_message = document.getElementById("error_message_" + u).innerHTML;
	
		csvrow.push(username, score, docname, elname); 
		if(error_message == ""){ //Ignore the data if there is any  error message
			var refTable = document.getElementById('table_' + u);
			var all_parts = refTable.querySelectorAll('tr');
			for (let r = 1; r < all_parts.length ; r++){ //excluding the first row
				if (r % 2 !== 0) {
					var part = all_parts[r].querySelectorAll('td'); // grab the part information within all parts
					for (let i = 0; i < part.length ; i++){
						if(column_info[i].className == "col_0") {
							csvrow.push(part[i].querySelectorAll('div')[0].getAttribute('value')); // add part name to the list if part name column exist
							csvrow.push(part[i].querySelectorAll('span')[0].innerHTML); // add material name to the list if part name column exist
						}
						else if(column_info[i].style.visibility == "collapse"){ //add blank cell to the collapsed column
							csvrow.push(""); 
						}
						else if(column_info[i].style.visibility != "collapse"){
							csvrow.push(part[i].innerHTML); 
						}
					}
				}
			}
		}
		csvrow.push(url);
		if(error_message != "") {
			csvrow.push(error_message);
		}
		csv_data.push(csvrow.join(",")); //Next row with properties
	}

	// Download
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