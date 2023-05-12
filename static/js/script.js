

function Logout() {
        fetch('/logout').then(response => {
            window.location.href = '/login';
        });
    }

function addEventListenersForIndex() {
  document.getElementById("file-uploader").addEventListener("change", function() {
    var formData = new FormData(document.getElementById("my-form"));
    fetch("/extract-file", {
      method: "POST",
      body: formData
    }).then(response => {
      if (response.ok) {
        // Enable the show statistics button
        const showStatisticsButton = document.getElementById("show-statistics-button");
        showStatisticsButton.disabled = false;
      }
    });
  });

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
    feedback.innerHTML = msg;
  });

  const showStatisticsButton = document.getElementById("show-statistics-button");
  showStatisticsButton.addEventListener("click", function() {
    // Read in the image and display the statistics
    const chartImage = document.getElementById("myChart");
    const img = document.createElement("img");
    img.src = chartImage.src;
    const statsContainer = document.getElementById("stats-container");
    statsContainer.appendChild(img);
  });
}




    const feedbackDiv = document.getElementById('feedback_file');
const observer = new MutationObserver(function(mutationsList) {
  for (let mutation of mutationsList) {
    if (mutation.type === 'childList' && feedbackDiv.innerText.trim() !== '') {
      // This function will be called whenever the content of the div changes
  changeButtonColor("mycontainer", "blue");
  removeButtonAttribute("mycontainer", "disabled");
  remove
      // Call your function here or execute any code you want to run when feedback is given
    }
  }
});

observer.observe(feedbackDiv, { childList: true });

document.getElementById("file_final").addEventListener("change", function(event) {
    event.stopPropagation();
    var file = this.files[0];
    var formData = new FormData();
    formData.append("file", file);
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







    function disableButton_final(buttonId) {
		    document.getElementById(buttonId).disabled = true;
		}

    function showLoading_final() {
			document.getElementById("spinner").style.display = "block";
		}

    function showText_final() {
        document.getElementById("loadingText").style.display = "block";
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
            changeButtonText("mycontainer", "Prediction Started..");
            showLoading("loading");
            fetch('/final/start_prediction')
                .then(response => {
                    hideLoading("loading");
                    hideText();
                    changeButtonColor("mycontainer", "green");
                    changeButtonColor("mycontain_download", "blue");
                    changeButtonText("mycontainer", "Prediction Finished");
                    removeButtonAttribute("mycontain_download", "disabled");
                    changeButtonColor("show_chart", "blue");
                    removeButtonAttribute("show_chart", "disabled");
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






    const button = document.getElementById("another");


button.addEventListener("click", function() {
  window.location.href = "/final";
});



