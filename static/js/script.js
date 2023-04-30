
function Logout() {
        fetch('/logout').then(response => {
            window.location.href = '/login';
        });
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




const feedbackDiv = document.getElementById('feedback');

const observer = new MutationObserver(function(mutationsList) {
  for (let mutation of mutationsList) {
    if (mutation.type === 'childList' && feedbackDiv.innerText.trim() !== '') {
      // This function will be called whenever the content of the div changes
  changeButtonColor("mycontain", "blue");
  removeButtonAttribute("mycontain", "disabled");
  remove
      // Call your function here or execute any code you want to run when feedback is given
    }
  }
});

observer.observe(feedbackDiv, { childList: true });



                    document.getElementById("file_final").addEventListener("change", function() {
    var file = this.files[0];
    var formData = new FormData();
    formData.append("file_final", file);
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/uploadfile/");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                document.getElementById("feedback_file").textContent = "File uploaded successfully. File name: " + file.name;
            } else if (xhr.readyState === 4 && xhr.status !== 200) {
                document.getElementById("feedback_file").textContent = "Error uploading file.";
            }
        };
    xhr.send(formData);
});




    function disableButton(buttonId) {
		    document.getElementById(buttonId).disabled = true;
		}

    function showLoading() {
			document.getElementById("spinner").style.display = "block";
		}
	function hideLoading() {
			document.getElementById("spinner").style.display = "none";
		}
    function showText() {
        document.getElementById("loadingText").style.display = "block";
    }
    function hideText() {
        document.getElementById("loadingText").style.display = "none";
    }
    function changeButtonColor(buttonId, color) {
            document.getElementById(buttonId).removeAttribute("style");
			document.getElementById(buttonId).setAttribute("class", "btn btn--radius-2 btn--"+color);
		}

    function removeButtonAttribute(buttonId, attribute) {
        document.getElementById(buttonId).removeAttribute(attribute);
    }

    function changeButtonText(buttonId, text) {
            const button = document.getElementById(buttonId);
            button.textContent = text;
     }



        function startPrediction() {
            changeButtonText("mycontain", "Prediction Started..");
            showLoading("loading");
            fetch('/final/start_prediction')
                .then(response => {
                    hideLoading("loading");
                    hideText();
                    changeButtonColor("mycontain", "green");
                    changeButtonColor("mycontain_download", "blue");
                    changeButtonText("mycontain", "Prediction Finished");
                    removeButtonAttribute("mycontain_download", "disabled");
                });
        }


  const downloadButton = document.getElementById('mycontain_download');
  downloadButton.addEventListener('click', () => {
    const url = '/download_prediction'; // The URL of your FastAPI endpoint
    fetch(url)
      .then(response => {
        const filename = response.headers.get('Content-Disposition').split('filename=')[1];
        response.blob().then(blob => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          a.click();
        });
      });
  });


    function showLoading() {
			document.getElementById("spinner").style.display = "block";
		}
	function hideLoading() {
			document.getElementById("spinner").style.display = "none";
		}
    function showList() {
           document.getElementById("logList").style.display = "inline-block";
		}
    function showRing() {
           document.getElementById("loading").style.display = "inline-block";
		}
    function showText() {
        document.getElementById("loadingText").style.display = "block";
    }
    function hideText() {
        document.getElementById("loadingText").style.display = "none";
    }
    function changeButtonColor(buttonId, color) {
			document.getElementById(buttonId).removeAttribute("style");
			document.getElementById(buttonId).setAttribute("class", "btn btn--radius-2 btn--"+color);

		}

    function removeButtonAttribute(buttonId, attribute) {
        document.getElementById(buttonId).removeAttribute(attribute);
    }

    function changeButtonText(buttonId, text) {
            const button = document.getElementById(buttonId);
            button.textContent = text;
    }

     function startTraining() {
         changeButtonText("trainButton", "Training Starting..");
         const intervalId = setInterval(refreshLog, 10000);
     }

     function disableButton() {
			document.getElementById("trainButton").disabled = true;
		}


    function refreshLog() {
      return fetch("/log")
        .then(response => response.json())
        .then(data => {
          const logList = document.getElementById("logList");
          data.log.forEach(line => {
            const li = document.createElement("li");
            currentStep++;
            li.textContent = line;
            logList.appendChild(li);
            animateProgress();

            if (li.textContent.includes('Training Complete')) {
              changeButtonColor("trainButton", "green");
              changeButtonText("trainButton", "Training Complete");
              changeButtonColor("resultsButton", "blue");
              removeButtonAttribute("resultsButton", "disabled");
              changeButtonColor("rerunButton", "blue");
              removeButtonAttribute("rerunButton", "disabled");
              changeButtonColor("annotateButton", "blue");
              removeButtonAttribute("annotateButton", "disabled");

              const interval = document.getElementById("intervalId");
              clearInterval(interval);
              return;
            } else if (logList.childElementCount >= 1) {
              showList();
              hideLoading();
              hideText();
              changeButtonText("trainButton", "Training Started");
            }
          });
        });
    }

      async function downloadFile() {
        const response = await fetch("/download");
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "results.json";
        document.body.appendChild(link);
        link.click();
        link.remove();
      }



    function loadJSON() {
      fetch('/download')
        .then(response => response.json())
        .then(data => showTable(data))
        .catch(error => console.error(error));
    }

function showTable(jsonData) {
  const container = document.getElementById("table-container");
  const table = document.createElement("table");

  // create table header
  const header = table.createTHead();
  const headerRow = header.insertRow();
  const iterationHeader = headerRow.insertCell();
  iterationHeader.innerHTML = "Pattern";
  const accHeader = headerRow.insertCell();
  accHeader.innerHTML = "Accuracy";
  const labelHeader = headerRow.insertCell();
  labelHeader.innerHTML = "Per label performance";

  // create table body
  const body = table.createTBody();
  for (let iteration in jsonData) {
    const row = body.insertRow();
    const iterationCell = row.insertCell();
    iterationCell.innerHTML = iteration;
    const accCell = row.insertCell();
    accCell.innerHTML = jsonData[iteration]["acc"];
    const labelCell = row.insertCell();
    const labelTable = document.createElement("table");
    const labelBody = labelTable.createTBody();
    for (let labelData of jsonData[iteration]["pre-rec-f1-supp"]) {
      const labelRow = labelBody.insertRow();
      const labelNameCell = labelRow.insertCell();
      const labelPerfCell = labelRow.insertCell();
      const labelDataArr = labelData.split(" ");
      labelNameCell.innerHTML = labelDataArr[0] + " " + labelDataArr[1];
      labelPerfCell.innerHTML = labelDataArr.slice(2).join(" ");
    }
    labelCell.appendChild(labelTable);
  }

  container.appendChild(table);
}



      function redirect() {
        window.location.href = "/final";
      }



    function runPythonCode() {
        fetch('/clean').then(response => {
            console.log('Python code executed successfully');
            window.location.href = '/basic';
        });
    }



    let steps;
    fetch('/steps').then(res => res.json()).then(data => parseInt(data.steps)).then(value => {steps = value});

    let currentStep = 0; // set the current step here, between 0 and steps
    const progressRing = document.querySelector('.progress-ring__circle--fill');
    const ring_circle = document.querySelector('.progress-ring__circle');
    const progressPercentage = document.querySelector('.progress-ring__percentage');
    const circumference = 2 * Math.PI * 45;
    let progress = 0;

    const animateProgress = () => {
      progress = currentStep / steps;
      progressRing.style.strokeDashoffset = circumference * (1 - progress) - circumference;
      progressPercentage.textContent = `${Math.floor(progress * 100)}%`;
    };



    const button = document.getElementById("another");

button.addEventListener("click", function() {
  window.location.href = "/final";
});
