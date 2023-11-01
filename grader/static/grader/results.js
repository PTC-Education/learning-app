var slidercontainer = document.getElementById('errorvalue');

function readSlider(slider){
  var slider = document.getElementById(slider);
  var resulttable= document.getElementById('resulttable');
  let data = [...resulttable.rows].map(t => [...t.children].map(u => u.innerText)) 
  var num=0;
  var numInSciNot=0;
  for (let i = 1; i < data.length; i++) {
    for(let j =1; j<4 ; j++){
      console.log("contol log of number",data[i][j]);
      num= Number(data[i][j]);
      resulttable.rows[i].cells[j].innerHTML = (num.toExponential(2).replace(/e\+?/, ' x 10^'));
    }
  }
}