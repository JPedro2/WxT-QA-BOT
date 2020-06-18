
    //grab the file input 
    const fileInput = document.getElementById('fileInput');
    //when the file input changes
    fileInput.onchange = () => {
        if (fileInput.files.length > 0) {
            //get the file name field
            const fileName = document.getElementById('fileName');
            //update the file name field
            fileName.textContent = fileInput.files[0].name;
            $('#deleteFileButton').removeAttr("disabled");

        }
    }

    //When a user types in the answer box call the preview function
    document.getElementById("ans").addEventListener("keyup", preview);

    //Generates markdown with showdown
    function preview() {
        //Import an instance of showdown
        var converter = new showdown.Converter();
        //Get the value of answer Field
        var text = document.getElementById('ans').value;
        //Convert the inputted text to HTML
        var html = converter.makeHtml(text);
        //set answerField to the updated html
        document.getElementById("answerField").innerHTML = html;
    };

    function generateQuestionFormat() {
        let listOfQuestions = document.getElementsByClassName('questionInput');
        let appendedQuestions = "";

        //loop through all the questions and generate the alternative questions 
        for (let i = 1; i < listOfQuestions.length; i++) {
            if (listOfQuestions[i].value != "") {
                if (listOfQuestions.length - 1 == i) {
                    appendedQuestions += listOfQuestions[i].value
                } else {
                    appendedQuestions += listOfQuestions[i].value + " ; ";
                }
            }
        }

        //If no alternative questions asked, return as "" as alternatives
        if (listOfQuestions.length == 1) {
            return ""
        }
        //returns the appended questions
        return appendedQuestions;
    }

    // Grab the forms id
    var form = document.getElementById('form');
    // Adds a listener for the "submit" event.
    form.addEventListener('submit', function (e) {
        e.preventDefault();
    });

    //On click of the submit button
    document.getElementById("submitQA").addEventListener('click', submitQA);
    //
    function submitQA() {
        //create a form for the updated QA
        var formdata = new FormData();
        //fill in the form details with the input values
        formdata.append("question", document.getElementsByClassName('questionInput')[0].value);
        formdata.append("answer", document.getElementById('ans').value);
        formdata.append("tag", document.getElementById('select').value);
        formdata.append("alternatives", generateQuestionFormat());

        var uploadedFile = $('#fileInput').prop('files')[0];

        if (uploadedFile !== undefined) {
        formdata.append("file", uploadedFile)
        }
        //set the requests settings
        var requestOptions = {
            method: 'POST',
            body: formdata,
            redirect: 'follow',
            mode: 'cors',
            headers: {
                "Authorization": 'Bearer ' + sessionStorage.getItem('token')
            }
        };
        //Execute POST
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
                //fire a successful
                //TODO: Check if actually successful
                //clear the fields
                clearFields();
            });
    }


    //function to clear the fields on the page
    function clearFields() {
        //delete the inputted files
        deleteFile()

        //reset the answer field to empty
        document.getElementById('ans').value = "";
        //set the topic dropdown to the default
        document.getElementById('select').value = 'General';

        //Grab all the questions to loop through 
        let listOfQuestions = document.getElementsByClassName('questionInput')

        //loop through all the questions on the field
        for (let i = 0; i < listOfQuestions.length; i++) {
            if (i == 0) {
                //set the first question field to empty string
                listOfQuestions[i].value = ""
            } else {
                //set all the alternative questions to null
                listOfQuestions[i].value = null;
            }

            //only remove if theres more than one
            if (listOfQuestions.length != 1) {
                //remove the extra question fields
                removeQuestionField(listOfQuestions);
            }
        }
    }

    //If add is clicked append a new input box to the page
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


    //If remove is clicked remove a input box unless theres only 1
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

    //function to delete the file on the page
    function deleteFile() {
        //get the file input and set value to undefined so it doesnt get uploaded
        document.getElementById('fileInput').value = "";
        document.getElementById('fileName').textContent = "No File Selected";
        $('#deleteFileButton').attr("disabled", true);

    }

    //function to remove the last question field on the page
    function removeQuestionField(listOfQuestionsInstance) {
        //if theres more than one question field we can remove it
        listOfQuestionsInstance[listOfQuestionsInstance.length - 1].remove();
    }