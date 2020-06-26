
// Flag to indicate if a file should be deleted on the database upon submit
let deleteFile = false;

// Context of locked icon at top right
const button = document.querySelector('#lockedIcon');

// ----------- First time visit tooltip -------------
// Context of tooltip which is only shown on first load
const tooltip = document.querySelector('#tooltip');
// Create a new tooltip
Popper.createPopper(button, tooltip, {
    placement: 'left',
    modifiers: [{
        name: 'offset',
        options: {
            offset: [0, 35],
        },
    },],
});

// Get the visited cache variable
var firstTimeBool = localStorage.getItem('firstTimeBool');

//If the user hasnt visited show tool tip
if (firstTimeBool == undefined) {
    $('#tooltip').fadeTo(12000, 100)
}

// Set the firstTimeBool flag so the tooltip doesn't appear next time
localStorage.setItem('firstTimeBool', 'true');

// --------------- Page lock/unlock -----------------
// Flag representing whether the page controls are locked
// True => Locked
// False => Unlocked
let lockedStatus = true;

let lockedIcon = document.getElementById('pageLocked');

var options = getAllQuestions().then(out => {
    return JSON.parse(out)
});
lockedIcon.addEventListener('click', function () {
    if (lockedStatus == true) {
        // If the page is locked, the user can unlock it if they are logged in
        let isLoggedIn = sessionStorage.getItem('token');

        if (isLoggedIn == null) {
            // The user has to be logged in to make changes, so fire an alert
            Swal.fire({
                title: 'Not Logged In!',
                text: "You need to log in to make changes.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: 'rgb(0, 188, 235)',
                cancelButtonColor: 'rgb(251, 61, 102)',
                confirmButtonText: 'Log In'
            }).then((result) => {
                if (result.value) {
                    location.href = './login'
                }
            })
        } else {
            // The user is logged in, so unlock the page
            // Create a new headers object to hold the check posture headers
            const myHeaders = new Headers();
            // Append the current token to the headers
            myHeaders.append("Authorization", 'Bearer ' + sessionStorage.getItem('token'));

            // Construct HTTP request
            const myRequest = new Request(baseURL + '/api/auth/checkPosture', {
                method: 'GET',
                headers: myHeaders,
                mode: 'cors',
                cache: 'default',
            });

            fetch(myRequest)
                .then(response => {
                    if (response.status == 401) {
                        Swal.fire({
                            title: 'Invalid Token!',
                            text: "Please log in again to continue.",
                            icon: 'warning',
                            showCancelButton: true,
                            confirmButtonColor: 'rgb(0, 188, 235)',
                            cancelButtonColor: 'rgb(251, 61, 102)',
                            confirmButtonText: 'Log In'
                        }).then((result) => {
                            if (result.value) {
                                location.href = './login'
                            }
                        })
                    } else {
                        // If the response is valid, unlock the page
                        lockedStatus = false
                        $('#lockedIcon').toggle()
                        $('#unlockedIcon').toggle('slow')
                        toggleInputLock(lockedStatus);
                    }
                })
        }
    } else {
        lockedStatus = true
        $('#lockedIcon').toggle('slow')
        $('#unlockedIcon').toggle()
        toggleInputLock(lockedStatus);
    }
})

// Function toggleInputLock() toggles the 'disabled' property of all inputs
function toggleInputLock(state) {
    if (state == false) {
        // If the state is changed to unlocked
        $('#addQuestionFieldButton').prop('disabled', false);
        $('#removeQuestionFieldButton').prop('disabled', false);
        $('#ans').prop('disabled', false);
        $('#select').prop('disabled', false);
        $('#fileInput').prop('disabled', false);
        $('#deleteFileButton').prop('disabled', false);
        $('#submitQA').prop('disabled', false);
        $('#deleteEntryButton').prop('disabled', false);
        $('.altQuestionInput').prop('disabled', false);

        ac.resultsList.render = false;

    } else {
        // If the state is changing to locked
        $('#addQuestionFieldButton').prop('disabled', true);
        $('#removeQuestionFieldButton').prop('disabled', true);
        $('#ans').prop('disabled', true);
        $('#select').prop('disabled', true);
        $('#fileInput').prop('disabled', true);
        $('#deleteFileButton').prop('disabled', true);
        $('#submitQA').prop('disabled', true);
        $('#deleteEntryButton').prop('disabled', true);
        $('.altQuestionInput').prop('disabled', true);

        ac.resultsList.render = true;
    }
}

// -------------- Search by Question ID -------------
document.getElementById("searchQuestionButton").addEventListener('click', function () {
    let questionID = document.getElementById("questionIDField").value;
    options.then(function (result) {
        populateFields(questionID);
    });
});

// --------------- All questions modal --------------
// Called when the user presses the all questions button
document.getElementById("getAllQuestion").addEventListener('click', function () {
    // Activate the modal by adding the active class
    document.getElementById("listModal").classList.add("is-active");
});
// Called when the user closes the model with the x
document.getElementById("closeQuestion").addEventListener('click', function () {
    // Close the modal by removing the active class
    document.getElementById("listModal").classList.remove("is-active");
});

// On page load, load all the questions and put them in the modal
axios.get(baseURL + '/api/getAll')
    .then(response => {
        // Loop through every q and a
        for (let i = 0; i < response.data.items.length; i++) {
            // Build html with the response
            let appendedQuestion = "<tr><td class='modalQuestionID'>" + response.data.items[i].id + "</td><td>" + response.data.items[i]
                .question + "</td></tr>";
            // Import them into the modal
            document.getElementById("anslist").innerHTML += appendedQuestion;
        }
    });

// Event listener on click of td 
$("body").on("click", "tr", function () {
    // Get the contex of what was clicked on
    populateFields($(this)[0].firstChild.innerHTML)
    document.getElementById("listModal").classList.remove("is-active");
});

//----------- ------- File input -------------------- 
const fileInput = document.getElementById('fileInput');
fileInput.onchange = () => {
    if (fileInput.files.length > 0) {
        const fileName = document.getElementById('fileName');
        fileName.textContent = fileInput.files[0].name;
        $('#deleteFileButton').removeAttr("disabled");
        deleteFile = false;
    }
}

// ------------ Answer markdown preview -------------
// When a user types in the answer box call the preview function
document.getElementById("ans").addEventListener("keyup", preview);

// Generate markdown preview with showdown library
function preview() {
    // Create an instance of showdown Converter object
    var converter = new showdown.Converter();
    // Get the value of answer Field
    var text = document.getElementById('ans').value;
    // Convert the inputted text to HTML using Converter object
    var html = converter.makeHtml(text);
    // Update the answerField to the generated HTML
    document.getElementById("answerField").innerHTML = html;
};

// -------- Generate alternative questions ----------
function generateQuestionFormat() {
    let listOfQuestions = document.getElementsByClassName('altQuestionInput');
    let appendedQuestions = "";

    // Loop through list of questions and generate alternatives 
    for (let i = 0; i < listOfQuestions.length; i++) {
        if (listOfQuestions.length - 1 == i) {
            appendedQuestions += listOfQuestions[i].value
        } else {
            appendedQuestions += listOfQuestions[i].value + " ; ";
        }
    }

    //If no alternative questions asked, return as "" as alternatives
    if (listOfQuestions.length == 0) {
        appendedQuestions = "empty";
    }
    return appendedQuestions;
}

// ---------- Submit question and answer ------------
// Listener for submit button
document.getElementById("submitQA").addEventListener('click', submitQA);

// Function submitQA() takes the form values and submits to API
function submitQA() {
    // Construct API endpoint from question ID
    var url = baseURL + "/api/updateEntries/" + document.getElementById('questionIDField').value

    // Deconstruct form values
    var formdata = new FormData();
    formdata.append("question", document.getElementsByClassName('questionInput')[0].value);
    formdata.append("answer", document.getElementById('ans').value);
    formdata.append("tag", document.getElementById('select').value);
    formdata.append("alternatives", generateQuestionFormat());
    formdata.append("deleteFile", deleteFile);

    // If there is an uploaded file to submit
    var uploadedFile = $('#fileInput').prop('files')[0];
    if (uploadedFile !== undefined) {
        formdata.append("file", uploadedFile)
    }

    // Construct the HTTP request
    var requestOptions = {
        method: 'PUT',
        body: formdata,
        redirect: 'follow',
        mode: 'cors',
        headers: {
            "Authorization": 'Bearer ' + sessionStorage.getItem('token')
        }
    };

    fetch(url, requestOptions)
        .then(response => {
            console.log(response)
            if (response.ok) {
                Swal.fire({
                    title: 'Thank you',
                    text: 'Submitted successfully',
                    icon: 'success',
                    showCancelButton: false,
                    confirmButtonColor: 'rgb(0, 188, 235)',
                    confirmButtonText: 'Continue'
                }).then((result) => {
                    if (result.value) {
                        location.href = './update'
                    }
                })
                return response.text()
            } else {
                return Promise.reject(response);
            }
        })
        .catch(error => {
            if (error.response.status === 401) {
                location.href = "./login"
            }
            if (error.response.status === 404) {
                location.href = "./login"
            }
            if (error.response.status === 400) {
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    text: 'Bad Request',
                })
            }
        })
}

// ------------ Add/remove alternatives -------------
// If add is clicked append a new input box to the page
document.getElementById("addQuestionFieldButton").addEventListener('click', function () {
    let altInputTemplate = $(
        '<div class="field questionInput"><input class="input altQuestionInput" type="text" placeholder="Alternative Question"></div>'
    )
        .hide()
        .fadeIn(300);
    $("#questionGroup").append(altInputTemplate);
    let currentHeight = $(".markdown").height()
    $(".markdown").height(currentHeight + 62)
})

// If remove is clicked remove a input box unless only one is left
document.getElementById("removeQuestionFieldButton").addEventListener('click', function () {
    var questionInputs = document.getElementsByClassName('questionInput');
    if (questionInputs.length > 1) {
        questionInputs[questionInputs.length - 1].remove();
        let currentHeight = $(".markdown").height()
        $(".markdown").height(currentHeight - 62)
    } else {
        alert("You must provide atleast one question.")
    }
})

// Function resetFields() sets all input fields to null
function resetFields() {
    document.getElementById("questionField").value = null;
    document.getElementById("ans").value = null;

    // Remove all alternative question input boxes
    var elements = document.getElementsByClassName('altQuestionInput');
    while (elements.length > 0) {
        // Delete each input box
        elements[0].parentNode.removeChild(elements[0]);
    }


}

// Function deleteFileFunction() removes a uploaded file
function deleteFileFunction() {
    // Get the file input and set value to undefined so it doesnt get uploaded
    document.getElementById('fileInput').value = "";
    document.getElementById('fileName').textContent = "No File Selected"
    $('#deleteFileButton').attr("disabled", true);
    deleteFile = true;
}

// ---------------- Delete question -----------------
function deleteEntry() {
    var qid = document.getElementById('questionIDField').value;
    // Fire a confirmation dialog
    Swal.fire({
        title: 'Are you sure you want to delete question ' + qid + '?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.value) {
            // Construct the API endpoint using question ID
            var url = baseURL + "/api/deleteQuestion/" + qid;
            // Construct the HTTP request
            var requestOptions = {
                method: 'DELETE',
                redirect: 'follow',
                mode: 'cors',
                headers: {
                    "Authorization": 'Bearer ' + sessionStorage.getItem('token')
                }
            };

            fetch(url, requestOptions)
                .then(response => response.text())
                .then(result => {
                    Swal.fire(
                        'Deleted!',
                        'Question ' + qid + ' has been deleted!',
                        'success'
                    )
                    location.reload();
                })
                .catch(error => {
                    if (error.status === 500) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops...',
                            text: 'Internal Server Error',
                        })
                    }
                    if (error.status === 400) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops...',
                            text: 'Bad Request',
                        })
                    }
                })
        }
    })
}

// --------------- Get all questions ----------------
function getAllQuestions() {
    var url = baseURL + "/api/getAllQuestions";

    // Construct the HTTP request
    var requestOptions = {
        method: 'GET',
        redirect: 'follow',
        mode: 'cors',
        headers: {
            "Authorization": 'Bearer ' + sessionStorage.getItem('token')
        }
    };

    return fetch(url, requestOptions)
        .then(response => response.text())
        .then(result => result)
        .catch(error => {
            if (error.status === 401) {
                location.href = "./login"
            }
            if (error.status === 400) {
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    text: 'Bad Request',
                })
            }
        })
}

// --------------- Populate input form --------------
function populateFields(questionID) {
    // Get database info by question ID 
    axios.get(baseURL + '/api/getKnowledge/' + questionID)
        .then(response => {
            if (response.status == 200) {
                // Update the question field on the page with the question queried
                document.getElementById("questionField").value = response.data.question;
                // Update the answer field on the page with the answer to the question
                document.getElementById("ans").value = response.data.answer;
                // Toggle button on the page
                if (response.data.location != null) {
                    document.getElementById("fileName").href = response.data.location;
                    document.getElementById("fileName").classList.remove("linkButton");
                    var fileNameArr = response.data.location.split('/');
                    document.getElementById("fileName").textContent = fileNameArr[fileNameArr.length - 1] +
                        ' - Open File'
                } else {
                    document.getElementById("fileName").classList.add("linkButton");
                    document.getElementById("fileName").textContent = "No Files Attached"
                }

                // Create markdown preview using showdown library
                var converter = new showdown.Converter();
                var text = response.data.answer;
                var html = converter.makeHtml(text);
                document.getElementById("answerField").innerHTML = html;

                document.getElementById("questionIDField").value = questionID;

                // Remove all existing alternative question fields
                $('.altQuestionInput').remove();

                // Print the alternative questions at the bottom of the page
                for (let i = 0; i < response.data.alternatives.length; i++) {
                    $("#questionGroup").append(
                        '<div class="field  questionInput"><input class="input altQuestionInput" disabled type="text" placeholder="Alternative Question" value="' +
                        response.data.alternatives[i] + '"></div>'
                    );

                    let currentHeight = $(".markdown").height()
                    $(".markdown").height(currentHeight + 62)
                }
                $(".to-hide").each(function (index) {
                    // Set each to visible
                    $(this).attr("style", "display:block !important;");
                });
            }
        }).catch(error => {
            console.log(error);
            if (error.response.status === 401) {
                location.href = "./login"
            }
            if (error.response.status === 400) {
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    text: 'Bad Request',
                })
            }
            if (error.response.status === 404) {
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    text: 'Question with ID ' + document.getElementById('questionIDField').value +
                        ' not found',
                })
            }
        })
}

// ------------------ Autocomplete ------------------
let ac = new autoComplete({
    // Use the list of all questions for autocompletion
    data: {
        src: options,
        key: ["question"],
        cache: false
    },
    placeHolder: "Enter a question",
    selector: "#questionField",
    threshold: 0,
    debounce: 300,
    searchEngine: "strict",
    resultsList: {
        render: true,
        container: source => {
            source.setAttribute("id", "question_list");
        },
        destination: document.querySelector("#questionField"),
        position: "afterend",
        element: "ul"
    },
    maxResults: 5,
    highlight: true,
    resultItem: {
        content: (data, source) => {
            source.innerHTML = data.match;
        },
        element: "li"
    },
    // When the autocomplete list is empty (no results)
    noResults: () => {
        const result = document.createElement("li");
        result.setAttribute("class", "no_result");
        result.setAttribute("tabindex", "1");
        result.innerHTML = "No Results";
        document.querySelector("#autoComplete_list").appendChild(result);
    },
    // When an object from the drop-down is selected, fill the input box and close the list
    onSelection: feedback => {
        $("#questionField").val(feedback.selection.value.question);
        $(".to-hide").each(function (index) {
            $(this).attr("style", "display:block !important;");
        });
        populateFields(feedback.selection.value.id);
    }

});

// Select the right list element when the enter key is pressed
var input = document.getElementById("questionIDField");
// Execute a function when the user releases a key on the keyboard
input.addEventListener("keyup", function (event) {
    // Number 13 is the "Enter" key on the keyboard
    if (event.keyCode === 13) {
        // Cancel the default action, if needed
        event.preventDefault();
        // Trigger the button element with a click
        document.getElementById("searchQuestionButton").click();
    }
});