

function compute_error(slider){

  var slider = document.getElementById(slider);
  var slider_text = document.getElementById('slider_value');
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
}