
    //Flag to indicate if a file should be deleted on the database upon submit.
    let deleteFile = false; 

    //Context of locked Icon at top tight
    const button = document.querySelector('#lockedIcon');

    //Context of tooltip which is only shown on first load
    const tooltip = document.querySelector('#tooltip');
    //Create a new tooltip
    Popper.createPopper(button, tooltip, {
        placement: 'left',
        modifiers: [{
            name: 'offset',
            options: {
                offset: [0, 35],
            },
        }, ],
    });

    //get the visited cache variable
    var firstTimeBool = localStorage.getItem('firstTimeBool');

    //If the user hasnt visited show tool tip
    if (firstTimeBool == undefined) {
        $('#tooltip').fadeTo(12000, 100)
        console.log("jel")
    }

    //tell the page i've visited 
    localStorage.setItem('firstTimeBool', 'true');



    //true = Page Locked
    //false = Page Unlocked
    let lockedStatus = true;

    let lockedIcon = document.getElementById('pageLocked');

    var options = getAllQuestions().then(out => {
        return JSON.parse(out)
    });

    lockedIcon.addEventListener('click', function () {
        if (lockedStatus == true) {
            let isLoggedIn = sessionStorage.getItem('token');

            if (isLoggedIn == null) {
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
                //Create a new headers object to hold the check posture headers
                const myHeaders = new Headers();
                //append the current token to the headers
                myHeaders.append("Authorization", 'Bearer ' + sessionStorage.getItem('token'));


                //Build out the request
                const myRequest = new Request( baseURL +'/api/auth/checkPosture', {
                    method: 'GET',
                    headers: myHeaders,
                    mode: 'cors',
                    cache: 'default',
                });

                console.log(myRequest)

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


    //function to toggle input locked status
    function toggleInputLock(state) {
        //if the state is changing to unlocked
        if (state == false) {
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

        } else { //if the state is changing to locked
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

    //Search by ID
    document.getElementById("searchQuestionButton").addEventListener('click', function () {
        let questionID = document.getElementById("questionIDField").value;
        options.then(function (result) {

            populateFields(questionID);

        });
    });

    //Called when the user presses the all questions button
    document.getElementById("getAllQuestion").addEventListener('click', function () {
        //activates the modal by adding the active class
        document.getElementById("listModal").classList.add("is-active");
    });
    //Called when the user closes the model with the x
    document.getElementById("closeQuestion").addEventListener('click', function () {
        //closes the modal by removing the active class
        document.getElementById("listModal").classList.remove("is-active");
    });

    //File input 
    const fileInput = document.getElementById('fileInput');
    fileInput.onchange = () => {
        if (fileInput.files.length > 0) {
            const fileName = document.getElementById('fileName');
            fileName.textContent = fileInput.files[0].name;
            $('#deleteFileButton').removeAttr("disabled");
            deleteFile = false;
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
        let listOfQuestions = document.getElementsByClassName('altQuestionInput');
        let appendedQuestions = "";

        //loop through all the questions and generate the alternative questions 
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
        console.log(appendedQuestions)
        //returns the appended questions
        return appendedQuestions;
    }

    // Grab the forms id
    var form = document.getElementById('form');

    //On click of the submit button
    document.getElementById("submitQA").addEventListener('click', submitQA);

    function submitQA() {
        var url = baseURL + "/api/updateEntries/" + document.getElementById('questionIDField').value

        var formdata = new FormData();
        formdata.append("question", document.getElementsByClassName('questionInput')[0].value);
        formdata.append("answer", document.getElementById('ans').value);
        formdata.append("tag", document.getElementById('select').value);
        formdata.append("alternatives", generateQuestionFormat());
        formdata.append("deleteFile", deleteFile);

        var uploadedFile = $('#fileInput').prop('files')[0];

        if (uploadedFile !== undefined) {
            formdata.append("file", uploadedFile)
        }

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

    //If add is clicked append a new input box to the page
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

    //If remove is clicked remove a input box unless theres only 1
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



    //reset all the fields to null
    function resetFields() {
        //set question field to null
        document.getElementById("questionField").value = null;

        //set answer field to null
        document.getElementById("ans").value = null;

        //remove all alternative question input boxes
        var elements = document.getElementsByClassName('altQuestionInput');
        while (elements.length > 0) {
            //delete each input box
            elements[0].parentNode.removeChild(elements[0]);
        }


    }

    function deleteFileFunction() {
        //get the file input and set value to undefined so it doesnt get uploaded
        document.getElementById('fileInput').value = "";
        document.getElementById('fileName').textContent = "No File Selected"
        $('#deleteFileButton').attr("disabled", true);
        deleteFile = true;

    }

    function deleteEntry() {
        var qid = document.getElementById('questionIDField').value;
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
                var url = baseURL + "/api/deleteQuestion/" + qid;

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

            //reload the current page
        })
    }

    function getAllQuestions() {
        var url = baseURL + "/api/getAllQuestions";

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

    function populateFields(questionID) {
        //Get request the question ID 
        axios.get(baseURL + '/api/getKnowledge/' + questionID)
            .then(response => {

                if (response.status == 200) {
                    //Update the question field on the page with the question queried
                    document.getElementById("questionField").value = response.data.question;
                    //Update the answer field on the page with the question queried
                    document.getElementById("ans").value = response.data.answer;
                    //Update the question type
                    // document.getElementById("type").textContent = response.data.tag;
                    //Toggles button on the page
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

                    var converter = new showdown.Converter();
                    //Get the value of answer Field
                    var text = response.data.answer;
                    //Convert the inputted text to HTML
                    var html = converter.makeHtml(text);
                    //set answerField to the updated html
                    document.getElementById("answerField").innerHTML = html;

                    document.getElementById("questionIDField").value = questionID;

                    //remove all the existing alt question fields
                    $('.altQuestionInput').remove();

                    //prints the alt questions at the bottom of the page
                    for (let i = 0; i < response.data.alternatives.length; i++) {
                        $("#questionGroup").append(
                            '<div class="field  questionInput"><input class="input altQuestionInput" disabled type="text" placeholder="Alternative Question" value="' +
                            response.data.alternatives[i] + '"></div>'
                        );

                        let currentHeight = $(".markdown").height()
                        $(".markdown").height(currentHeight + 62)
                    }
                    $(".to-hide").each(function (index) {
                        //set them to visible
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



    let ac = new autoComplete({

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
        noResults: () => {
            const result = document.createElement("li");
            result.setAttribute("class", "no_result");
            result.setAttribute("tabindex", "1");
            result.innerHTML = "No Results";
            document.querySelector("#autoComplete_list").appendChild(result);
        },
        onSelection: feedback => {
            $("#questionField").val(feedback.selection.value.question);
            $(".to-hide").each(function (index) {
                $(this).attr("style", "display:block !important;");
            });
            populateFields(feedback.selection.value.id);
        }

    });


    // ------------------------- Question Search ---------------------------------

    //--------- Event Listener for Enter Search ------------
    // Get the input field
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

  


    // --------------------- All Questions Modal Code ----------------------------
    //On page load load all the questions and put them in the modal
    axios.get(baseURL + '/api/getAll')
        .then(response => {
            //Loop through every q and a
            for (let i = 0; i < response.data.items.length; i++) {
                //build html with the response
                let appendedQuestion = "<tr><td class='modalQuestionID'>" + response.data.items[i].id + "</td><td>" + response.data.items[i]
                    .question + "</td></tr>";
                //import them into the modal
                document.getElementById("anslist").innerHTML += appendedQuestion;
            }
    });

    //Add an event listener on click of td 
    $("body").on("click", "tr", function() {
        //Get the contex of what was clicked on
        populateFields($(this)[0].firstChild.innerHTML) 
        document.getElementById("listModal").classList.remove("is-active");
    });