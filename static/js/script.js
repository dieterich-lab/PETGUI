
function pageLoad() {
    $.LoadingOverlay("show");
}

function hideLoad() {
    $.LoadingOverlay("hide");
}

function Logout() {
    fetch('/logout').then(response => {
        hideLoad();
        window.location.href = '/login?logout=True';
    });
}

function Login() {
    fetch('/login').then(response => {
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
        fillLabels();
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
  const chartImage = document.getElementById("myChart");
  const statsContainer = document.getElementById("stats-container");

  // If the chart is currently visible, hide it and change the button name
  if (chartImage.style.display === "block") {
    chartImage.style.display = "none";
    showStatisticsButton.textContent = "View Data";
    statsContainer.innerHTML = ""; // Clear the statistics container
  } else {
    // If the chart is currently hidden, show it and change the button name
    chartImage.style.display = "block";
    showStatisticsButton.textContent = "Hide Data";
    const img = document.createElement("img");
    img.src = chartImage.src;
    statsContainer.appendChild(img);
  }
});
}


var counter = 1;

function addInput_new() {
    var inputFields = document.querySelectorAll('#template-input .input-group');
    if (inputFields.length > 0) {
        var lastInputField = inputFields[inputFields.length-1];
        var addButton = lastInputField.querySelector('.add-btn');
        if (addButton) {
            addButton.textContent = "-";
            addButton.setAttribute("onClick", "removeSpecificInput(this);");
        }

        var trashButton = lastInputField.querySelector('.trash-btn');
        if (trashButton) {
            trashButton.parentNode.removeChild(trashButton);
        }
    }

    var newdiv = document.createElement('div');
    newdiv.className = "input-group";
    newdiv.innerHTML = "<input class='input--style-5 form-control' type='text' placeholder='New template' name=template_"+ counter +" required> <button class='btn btn--radius-2 btn--blue add-btn add-remove-btn' style='padding: 0 25px;' type='button' onClick='addInput_new();'>+</button> <button class='btn btn--radius-2 btn--grey trash-btn add-remove-btn' style='padding: 0 15px; font-size: 0.9rem;' type='button' onClick='removeInput(this);'>🗑️</button>";
    var container = document.getElementById('template-input');
    container.appendChild(newdiv);
    container.appendChild(document.createElement('br'));
    counter++;
}

function removeInput(button) {
    var inputField = button.parentNode;
    var brElement = inputField.nextSibling;
    inputField.parentNode.removeChild(inputField);
    brElement.parentNode.removeChild(brElement);
    counter--;

    adjustLastInput();
}

function removeSpecificInput(button) {
    var inputField = button.parentNode;
    var brElement = inputField.nextSibling;
    inputField.parentNode.removeChild(inputField);
    brElement.parentNode.removeChild(brElement);
    counter--;

    adjustLastInput();
}

function adjustLastInput() {
    var inputFields = document.querySelectorAll('#template-input .input-group');
    if (inputFields.length > 0) {
        var lastInputField = inputFields[inputFields.length-1];
        var removeButton = lastInputField.querySelector('.remove-btn');
        if (removeButton) {
            removeButton.textContent = "+";
            removeButton.className = "btn btn--radius-2 btn--blue add-btn add-remove-btn";
            removeButton.setAttribute("onClick", "addInput_new();");
        }

        var existingTrashButtons = lastInputField.querySelectorAll('.trash-btn');
        if (existingTrashButtons.length > 1) {
            for (var i = 0; i < existingTrashButtons.length - 1; i++) {
                existingTrashButtons[i].parentNode.removeChild(existingTrashButtons[i]);
            }
        }

        if (inputFields.length === 1) {
            var trashButton = lastInputField.querySelector('.trash-btn');
            if (trashButton) {
                trashButton.parentNode.removeChild(trashButton);
            }
        }
    }
}








var counter_map = 0;
var dynamicInput = [];

function addInput_map(label) {
    var newdiv = document.createElement("div");
    var currentCounter = counter_map;
    newdiv.id = "mapping_" + currentCounter;
    newdiv.innerHTML = "Mapping " + (currentCounter + 1)  + " <div class='row row-space'><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' value="+ label +" name='origin_" + currentCounter + "' required></div></div><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' name='mapping_" + currentCounter + "' placeholder='verbalizer " + (currentCounter + 1) +"' required></div></div></div>";
    document.getElementById('formularmap').appendChild(newdiv);
    dynamicInput.push("mapping_" + currentCounter);
    counter_map++;
}


// var counter_map = 0;
// var dynamicInput = [];
//
// function addInput_map(label) {
//     var newdiv = document.createElement("div");
//     var currentCounter = counter_map;
//     newdiv.id = "mapping_" + currentCounter;
//     newdiv.innerHTML = "Mapping " + (currentCounter + 1)  + " <div class='row row-space'><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' value="+ label +" name='origin_" + currentCounter + "' required></div></div><div class='col-2'><div class='input-group'><input class='input--style-5 form-control' type='text' name='mapping_" + currentCounter + "' placeholder='verbalizer " + (currentCounter + 1) +"' required><div id='error_message_" + currentCounter + "' style='color: red;'></div></div></div></div>";
//     document.getElementById('formularmap').appendChild(newdiv);
//     dynamicInput.push("mapping_" + currentCounter);
//     counter_map++;
// }




// // This function is called when the form is submitted
// async function check_vocab_on_submit(event) {
//     // Initialize a variable to check if any word is not in vocab
//     var isInVocab = true;
//
//     for (let input of dynamicInput) {
//         var word = document.getElementsByName(input)[0].value;  // get the value from input field
//
//         // create a new HTTP request
//         var xhr = new XMLHttpRequest();
//         xhr.open("POST", "/check_vocab", false);  // make it synchronous
//         xhr.setRequestHeader("Content-Type", "application/json");
//
//         // convert data to JSON format and send it to the server
//         var data = JSON.stringify({"word": word});
//         xhr.send(data);
//
//         if (xhr.status === 200) {
//             document.getElementById("error_message_" + input.split('_')[1]).innerHTML = "";  // clear error message
//         } else if (xhr.status === 422) {
//             var error_message = JSON.parse(xhr.responseText).detail;  // parse the error message
//             document.getElementById("error_message_" + input.split('_')[1]).innerHTML = error_message;  // display the error message
//             isInVocab = false;  // mark that a word is not in vocab
//         }
//     }
//
//     // If any word is not in vocab, prevent the form submission
//     if (!isInVocab) {
//         event.preventDefault();  // prevent the form from being submitted
//     }
// }

// Add the event listener to the form
//document.getElementById('my-form').addEventListener('submit', check_vocab_on_submit);



    const feedbackDiv = document.getElementById('feedback_file');
const observer = new MutationObserver(function(mutationsList) {
  for (let mutation of mutationsList) {
    if (mutation.type === 'childList' && feedbackDiv.innerText.trim() !== '') {
      // This function will be called whenever the content of the div changes
  changeButtonColor("mycontainer", "blue");
  removeButtonAttribute("mycontainer", "disabled");
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





    function disableButton_final(buttonId) {
		    document.getElementById(buttonId).disabled = true;
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

     function createArrayOfLabels(labels) {
          var result = [];
          labels.forEach(function (label) {
            result.push(label);
          return result;
        });
    }

     function fillLabels() {
        fetch('/report-labels')
            .then(response => response.json())
            .then(data => {
            var result = [];
            data.list.forEach(lab => {
            result.push(lab);
            });
            result.sort();
            result.forEach(function(label) {
                addInput_map(label);
            });
        });
    }



    function checkPrediction() {
        fetch('final/start_prediction');
        changeButtonText("mycontainer", "Prediction Started..");
        const predictInt = setInterval(check, 10000);
    }

    function check() {
        fetch('/final/start_prediction?check=True')
            .then(response => response.json())
            .then(data => {
                if (data.status == "CD") {
                hideLoading();
                hideText();
                changeButtonColor("mycontainer", "green");
                changeButtonColor("mycontain_download", "blue");
                changeButtonText("mycontainer", "Prediction Finished");
                removeButtonAttribute("mycontain_download", "disabled");
                changeButtonColor("show_chart", "blue");
                removeButtonAttribute("show_chart", "disabled");
                }
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

    function hideAbort() {
        document.getElementById("abortButton").style.display = "none";
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
              const btn = document.getElementById("abortButton");
              if (btn.checked) {
                  btn.style.display = "none";
              }
              changeButtonColor("trainButton", "green");
              changeButtonText("trainButton", "Training Complete");
              removeButtonAttribute("resultsButton", "disabled");
              removeButtonAttribute("rerunButton", "disabled");
              removeButtonAttribute("annotateButton", "disabled");

              const interval = document.getElementById("intervalId");
              clearInterval(interval);
              return;
            } else if (logList.childElementCount >= 1) {
              document.getElementById("progress-ring-div").style.display = "flex";
              document.getElementById("Prog-text").style.display = "flex";
              document.getElementById("Log-text").style.display = "inline-block";
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



    // New function to send a POST request to the FastAPI server
async function loadJSON() {
  try {
    // First, send a POST request to '/label-change' and wait for it to complete
    await fetch('/label-change', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
    });

    // After the POST request is complete, fetch and process the JSON file
    const response = await fetch('/download');
    const data = await response.json();
    showTable(data);
  } catch (error) {
    console.error(error);
  }
}




function showTable(jsonData) {
  const container = document.getElementById("table-container");
  const table = document.createElement("table");
  table.style.width = "100%"; // 设置表格宽度

  // Create colgroups
  const colgroup = document.createElement('colgroup');
  const col1 = document.createElement('col');
  const col2 = document.createElement('col');
  const col3 = document.createElement('col');
  col1.style.width = '20%';
  col2.style.width = '20%';
  col3.style.width = '60%';
  colgroup.appendChild(col1);
  colgroup.appendChild(col2);
  colgroup.appendChild(col3);
  table.appendChild(colgroup);

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


  if (jsonData.hasOwnProperty("Final")) {
    const row = body.insertRow();
    const iterationCell = row.insertCell();
    iterationCell.innerHTML = "Final";
    const accCell = row.insertCell();
    accCell.innerHTML = jsonData["Final"]["acc"];
    const labelCell = row.insertCell();
    const labelTable = document.createElement("table");
    labelTable.style.width = "100%";
    const labelBody = labelTable.createTBody();
    for (let labelData of jsonData["Final"]["pre-rec-f1-supp"]) {
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


    function redirectHome() {
        fetch('/clean').then(response => {
            hideLoad();
            window.location.href = '/start';
        });
    }

    function redirectNewConf() {
        fetch('/clean').then(response => {
        hideLoad();
            window.location.href = '/basic';
        });
    }


    const button = document.getElementById("another");


button.addEventListener("click", function() {
  window.location.href = "/final";
});











