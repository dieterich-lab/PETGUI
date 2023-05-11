
var counter = 1;
var dynamicInput_1 = [];

 function addInput(){
    var newdiv = document.createElement('div');
    newdiv.id = dynamicInput_1[counter];
    newdiv.innerHTML = "Template " + (counter + 1) + " <br><input class='input--style-5 form-control' type='text' placeholder='Next template text' name = template_"+counter +" required> <br><input class='btn btn--radius-2 btn--blue' style='padding: 0 25px;' type='button' value='-' onClick='removeInput("+dynamicInput_1[counter]+");'>";
    document.getElementById('formulario').appendChild(newdiv);
    counter++;
}

  function removeInput(id){
    var elem = document.getElementById(id);
    counter--;
    return elem.parentNode.removeChild(elem);
  }

  var counter_map = 2;
var dynamicInput = [];


function addInput_map(){
    var newdiv = document.createElement('div');
    newdiv.id = dynamicInput[counter_map];
    newdiv.innerHTML = "Mapping " + (counter_map + 1) +
    " <div class='row row-space'><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' placeholder='origin' name=origin_"+ counter_map +" required></div></div><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' placeholder='mapping' name=mapping_"+counter_map+" required><input class='btn btn--radius-2 btn--blue' style='padding: 0 25px' type='button' value='-' onClick='removeInput("+dynamicInput[counter]+");'></div></div></div>";
    document.getElementById('formularmap').appendChild(newdiv);
    counter_map++;
}
