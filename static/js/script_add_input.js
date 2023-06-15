var counter = 1;
var dynamicInput_1 = [];

function addInput_new() {
    var newdiv = document.createElement('div');
    var currentCounter = counter;
    newdiv.id = "template_" + currentCounter;
    newdiv.innerHTML = "Template " + (currentCounter + 1) + " <br><div class=\"input-group\"><input class='input--style-5 form-control' type='text' placeholder='A test that it is changing' name='template_" + currentCounter + "' required> <br><button class='btn btn--radius-2 btn--blue' style='padding: 0 25px;' type='button' value='-' onClick='removeInput(\"template_" + currentCounter + "\");'>-</button></div>";
    document.getElementById('template input').appendChild(newdiv);
    dynamicInput_1.push("template_" + currentCounter);
    counter++;
}

function removeInput(id) {
    var elem = document.getElementById(id);
    elem.parentNode.removeChild(elem);

    if (id.startsWith("template_")) {
        var index = dynamicInput_1.indexOf(id);
        if (index > -1) {
            dynamicInput_1.splice(index, 1);
        }
        counter--;
    } else if (id.startsWith("mapping_")) {
        var index = dynamicInput.indexOf(id);
        if (index > -1) {
            dynamicInput.splice(index, 1);
        }
        counter_map--;
    }
}



var counter_map = 2;
var dynamicInput = [];

function addInput_map() {
    var newdiv = document.createElement('div');
    var currentCounter = counter_map;
    newdiv.id = "mapping_" + currentCounter;
    newdiv.innerHTML = "Mapping " + (currentCounter + 1) + " <div class='row row-space'><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' placeholder='origin' name='origin_" + currentCounter + "' required></div></div><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' placeholder='mapping' name='mapping_" + currentCounter + "' required><input class='btn btn--radius-2 btn--blue' style='padding: 0 25px' type='button' value='-' onClick='removeInput(\"mapping_" + currentCounter + "\");'></div></div></div>";
    document.getElementById('formularmap').appendChild(newdiv);
    dynamicInput.push("mapping_" + currentCounter);
    counter_map++;
}



