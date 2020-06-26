// ------------ Handler for file input --------------
const fileInput = document.getElementById('fileInput');
// When the file input changes:
fileInput.onchange = () => {
    if (fileInput.files.length > 0) {
        // Get the file name field
        const fileName = document.getElementById('fileName');
        // Update the file name field
        fileName.textContent = fileInput.files[0].name;
        // Enable the delete file button
        $('#deleteFileButton').removeAttr("disabled");
    }
}

// ------------ Markdown preview handler ------------
// When a user types in the answer box call the preview function
document.getElementById("ans").addEventListener("keyup", preview);

// Function preview() generates markdown with showdown library
function preview() {
    // Import an instance of showdown
    var converter = new showdown.Converter();
    // Get the value of answer field
    var text = document.getElementById('ans').value;
    // Convert the inputted text to HTML so it can be displayed properly in the browser
    var html = converter.makeHtml(text);
    // Set answerField to the converted HTML
    document.getElementById("answerField").innerHTML = html;
};

// ------- Generating alternative questions ---------
// Function generateQuestionFormat() 
function generateQuestionFormat() {
    let listOfQuestions = document.getElementsByClassName('questionInput');
    let appendedQuestions = "";

    // Loop through all questions and generate alternatives 
    for (let i = 1; i < listOfQuestions.length; i++) {
        if (listOfQuestions[i].value != "") {
            if (listOfQuestions.length - 1 == i) {
                appendedQuestions += listOfQuestions[i].value
            } else {
                appendedQuestions += listOfQuestions[i].value + " ; ";
            }
        }
    }

    // If no alternative questions asked, return as ""
    if (listOfQuestions.length == 1) {
        return ""
    }
    return appendedQuestions;
}

// ------------- Form submit listener ---------------
var form = document.getElementById('form');
form.addEventListener('submit', function (e) {
    // Prevent default form behaviour
    e.preventDefault();
});

// On click of the submit button
document.getElementById("submitQA").addEventListener('click', submitQA);
// Function submitQA() populates the form and executes HTTP POST
function submitQA() {
    // Create a form for the updated QA
    var formdata = new FormData();
    // Populate the form with the input values
    formdata.append("question", document.getElementsByClassName('questionInput')[0].value);
    formdata.append("answer", document.getElementById('ans').value);
    formdata.append("tag", document.getElementById('select').value);
    formdata.append("alternatives", generateQuestionFormat());

    // If there is an uploaded file, add it to the form
    var uploadedFile = $('#fileInput').prop('files')[0];
    if (uploadedFile !== undefined) {
        formdata.append("file", uploadedFile)
    }

    // Set the request settings
    var requestOptions = {
        method: 'POST',
        body: formdata,
        redirect: 'follow',
        mode: 'cors',
        headers: {
            "Authorization": 'Bearer ' + sessionStorage.getItem('token')
        }
    };
    // Execute POST
    fetch(baseURL + "/api/addEntry", requestOptions)
        .then(response => {
            console.log(response)
            if (response.ok) {
                Swal.fire(
                'Thank you',
                'Submitted successfully',
                'success'
            )
            return response.text()
            } else {
                return Promise.reject(response);
            }
        })
        .catch(error => {
            console.log(error)
            if (error.status === 401) {
                location.href = "./login"
            }
            if (error.status === 404) {
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
        .then(response => {
            // Clear form fields
            clearFields();
        });
}

// Function clearFields() depopulates/resets the form
function clearFields() {
    // Delete inputted file
    deleteFile()

    // Reset the answer field to empty
    document.getElementById('ans').value = "";
    // Set the topic dropdown to the default
    document.getElementById('select').value = 'General';

    // Grab all the questions to loop through 
    let listOfQuestions = document.getElementsByClassName('questionInput')

    // Loop through all the questions in the field
    for (let i = 0; i < listOfQuestions.length; i++) {
        if (i == 0) {
            // Set the first question field to empty
            listOfQuestions[i].value = ""
        } else {
            // Set all alternative questions to null
            listOfQuestions[i].value = null;
        }

        // Only remove if theres more than one
        if (listOfQuestions.length != 1) {
            // Remove the extra question fields
            removeQuestionField(listOfQuestions);
        }
    }
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
    $(".markdown").height(currentHeight + 52)
})


// If remove is clicked remove an input box, unless only one is left
document.getElementById("removeQuestionFieldButton").addEventListener('click', function () {
    var questionInputs = document.getElementsByClassName('questionInput');
    if (questionInputs.length > 1) {
        questionInputs[questionInputs.length - 1].remove();
        let currentHeight = $(".markdown").height()
        $(".markdown").height(currentHeight - 52)
    } else {
        alert("You must provide atleast one question.")
    }
})

// Function deleteFile() deletes the uploaded file
function deleteFile() {
    // Get the file input and set value to undefined so it doesnt get uploaded
    document.getElementById('fileInput').value = "";
    document.getElementById('fileName').textContent = "No File Selected";
    $('#deleteFileButton').attr("disabled", true);

}

// Function removeQuestionField() deletes the last question field on the page
function removeQuestionField(listOfQuestionsInstance) {
    // If there is more than one question field, remove it
    listOfQuestionsInstance[listOfQuestionsInstance.length - 1].remove();
}