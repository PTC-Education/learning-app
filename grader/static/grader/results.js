

function compute_error(slider,number){
  var slider = document.getElementById(slider);
  document.getElementById('slider_value').innerHTML=slider.value;
  error=Number(slider.value);
  var resulttable= document.getElementById("reference");
  let data = [...resulttable.rows].map(t => [...t.children].map(u => u.innerText)) ;  
  var ref_mass= Number(data[1][0]);
  var ref_vol = Number(data[1][1]);
  var ref_surf=Number(data[1][2]);


  for (let i=0; i<number;i++ ){
    var resulttable= document.getElementById("table_"+i);
    let data = [...resulttable.rows].map(t => [...t.children].map(u => u.innerText)) ;  
    
    var error_mass= Math.abs(Number(data[1][0]) - ref_mass) * 100 /  ref_mass; 
    var error_vol=Math.abs(Number(data[1][1]) - ref_vol) * 100 /  ref_vol;
    var error_surf=Math.abs(Number(data[1][2]) - ref_surf) * 100 /  ref_surf;

    //console.log("Errors", error_mass,error_vol,error_surf, "and error is ",error);
    //console.log("Type",typeof(Math.abs(Number(data[1][1]) -  ref_vol /  ref_vol)));
    //console.log("Type of error",typeof(error));
    if (error_mass >  error) {
      resulttable.rows[2].cells[0].innerHTML="&#x274C;";
    }
    else{
      resulttable.rows[2].cells[0].innerHTML="&#x2705;";
    }
    if (error_vol >  error) {
      resulttable.rows[2].cells[1].innerHTML="&#x274C";
    }
    else{
      resulttable.rows[2].cells[1].innerHTML="&#x2705;";
    }
    if (error_surf >  error) {
      resulttable.rows[2].cells[2].innerHTML="&#x274C";
    }
    else{
      resulttable.rows[2].cells[2].innerHTML="&#x2705;";
    }
  }
  //var resulttable= document.getElementById("1");
  //let data = [...resulttable.rows].map(t => [...t.children].map(u => u.innerText)) ;  
  //console.log(data);

/*
  var resulttable= document.getElementById('resulttable');
  let data = [...resulttable.rows].map(t => [...t.children].map(u => u.innerText)) ;  

  error=Number(slider.value);
  slider_text.innerHTML=slider.value;
  var num=0;
  for (let i = 2; i < data.length; i=i+2) {
    for(let j =2; j<4 ; j++){      
      if (Math.abs(Number(data[i][j]) - Number(data[1][j])) /  Number(data[1][j]) >  error) {
        resulttable.rows[i+1].cells[j].innerHTML="&#x2717;";
      }
      else{
        resulttable.rows[i+1].cells[j].innerHTML="&#x2713;"; 
      }
    }
  }
  */
}