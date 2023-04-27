
function Logout() {
        fetch('/logout').then(response => {
            window.location.href = '/login';
        });
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

  function removeInput(id){
    var elem = document.getElementById(id);
    counter_map--;
    return elem.parentNode.removeChild(elem);
  }

   const fileUploader = document.getElementById('file-uploader');
fileUploader.addEventListener('change', (event) => {
    const files = event.target.files;
    console.log('files', files);
    const feedback = document.getElementById('feedback');
    const fileExt = files[0].name.split('.').pop(); // Get the file extension
    if (fileExt !== 'gz') { // Check if file is not a tar.gz file
        feedback.innerHTML = `Error: ${fileExt} file type not supported!`;
        return;
    }
    const msg = `File ${files[0].name} uploaded successfully!`;
    feedback.innerHTML = msg;});

  document.getElementById("file-uploader").addEventListener("change", function() {
    var formData = new FormData(document.getElementById("my-form"));
    fetch("/extract-file", {
      method: "POST",
      body: formData
        }).then(response => {
        if (response.ok) {
          // Show the chart container and reload the image
          const chartContainer = document.getElementById("chart-container");
          chartContainer.style.display = "block";
          const chartImage = document.getElementById("myChart");
          chartImage.src = "static/chart.png?" + new Date().getTime();
        }
    });
  });



