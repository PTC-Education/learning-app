var slidercontainer = document.getElementById('errorvalue');

function readSlider(slider){
  console.log("this is me");
  var slider = document.getElementById(slider);
  console.log("directly from slider",slider.value);
  var resulttable= document.getElementById('resulttable');
  console.log(resulttable);
    let data = [...resulttable.rows].map(t => [...t.children].map(u => u.innerText)) 
    console.log(data);
    for (let i = 0; i < data.length; i++) {
      for (let j=0;j<data[i].length; j++){
        console.log("important")
      //console.log(data[i][j])
      }
    }

resulttable.rows[2].cells[1].innerHTML = 'Hello';

}






