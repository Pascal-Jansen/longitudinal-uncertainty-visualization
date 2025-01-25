function getUserData() {
    var userID = document.getElementById('userID').value;
    var request = new XMLHttpRequest();
    request.open('POST', '/getQuestionnaire', true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.onload = function() {
        if (this.status >= 200 && this.status < 400) {
            var resp = JSON.parse(this.response);
            
            if (resp.error) {
                document.getElementById('questionnaireArea').innerHTML = '<h2>' + resp.error + '</h2>';
            } 
            
            if (resp.questionnaire) {
                document.getElementById('questionnaireArea').innerHTML = '<h2>Next Questionnaire: ' + resp.questionnaire + '</h2>';
                // Display the corresponding questionnaire link or redirect the user
            }
            
            if(resp.progress) {
                updateProgressTable(resp.progress); // if progress was updated
                toggleVisibility('progressArea', 'block');
            }
            
        } else {
            document.getElementById('questionnaireArea').innerHTML = '<h2>There was an error downloading your data.</h2>';
        }
    };
    request.onerror = function() {
        document.getElementById('questionnaireArea').innerHTML = '<h2>There was an error downloading your data.</h2>';
    };

    // Get the local date and time
    var localDateTime = new Date();
    
    // Get the user's time zone (IANA time zone string)
    var timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Send the request with localTime and timeZone
    request.send(JSON.stringify({
        userID: userID, 
        localTime: localDateTime.toLocaleString('en-GB'), 
        timeZone: timeZone
    }));

    document.querySelector('#infoArea .info').style.display = 'none';
    document.querySelector('#toggleButton').textContent = 'Show Information';
}

function updateProgressTable(data) {
    var curr_cell = parseInt(data.cell);

    if(curr_cell > 0) {
        for (var i = 0; i <= curr_cell; i++) {
            document.getElementById("cell_" + i).innerText = "Done"; // set previous cells
        }
    }

    if(curr_cell >= 0 && curr_cell <= 5) {
        document.getElementById("cell_" + curr_cell).innerText = data.content; // set current cell
    }

    if(data.content != "Running" && curr_cell > 0) {
        var next_cell = curr_cell + 1;
        if(next_cell <= 5) {
            document.getElementById("cell_" + next_cell).innerText = "Waiting"; // set next cell
        }
    }
}

function startTimer(timeInSeconds) {
    var timerElement = document.getElementById("timerArea");
    timerElement.innerHTML = "The next questionnaire will be available in " + formatTime(timeInSeconds) + ".";

    var countdown = setInterval(function() {
        timeInSeconds--;

        if (timeInSeconds <= 0) {
            clearInterval(countdown);
            timerElement.innerHTML = "The next questionnaire is now available.";
            // Hier können Sie weitere Aktionen durchführen, z. B. den Benutzer umleiten
        } else {
            timerElement.innerHTML = "The next questionnaire will be available in " + formatTime(timeInSeconds) + ".";
        }
    }, 1000);
}

function formatTime(timeInSeconds) {
    var minutes = Math.floor(timeInSeconds / 60);
    var seconds = timeInSeconds % 60;
    return minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
}

function toggleVisibility(id, mode) {
    var div = document.getElementById(id);
    div.style.display = mode;
}

function toggleInfoArea(state) {
    var infoArea = document.querySelector('#infoArea .info');
    var toggleButton = document.querySelector('#toggleButton');
    if (infoArea.style.display === 'none') {
        infoArea.style.display = 'block';
        toggleButton.textContent = 'Hide Information';
    } else {
        infoArea.style.display = 'none';
        toggleButton.textContent = 'Show Information';
    }
}

function updateClock() {
    const now = new Date();
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const timeString = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const dateString = now.toLocaleDateString('en-GB');
    document.getElementById('clock').textContent = `${dateString} ${timeString} (${timeZone})`;
}

// Update the clock immediately and then every second
updateClock();
setInterval(updateClock, 1000);