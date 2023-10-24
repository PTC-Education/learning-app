var formfield = document.getElementById('doc_field_form');


function add_list(doc){
  var newField = document.createElement('input');
  newField.setAttribute('type','text');
  newField.setAttribute('name','doc');
  newField.setAttribute('class','text');
  newField.setAttribute('size',50);
  newField.setAttribute('placeholder',doc);
  formfield.appendChild(newField);

}