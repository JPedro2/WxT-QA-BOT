    $(document).ready(function() {
        $('#loginbtn').click(function(e) {
            // Prevent default form behaviour
            e.preventDefault();

            // Get login credentials
            var credentials = $('#login').serializeArray();
            var username = credentials[0].value;
            var password = credentials[1].value;
            var duration;
            var token;

            // Create Headers object for the HTTP request
            var myHeaders = new Headers();
            // Concatenate the username and password and base64 encode for Basic Authentication
            var to_encode = username+":"+password;
            var base64_encoded = btoa(to_encode);
            myHeaders.append("Authorization", "Basic "+base64_encoded);
            myHeaders.append("Access-Control-Allow-Origin", "*");

            var requestOptions = {
                method: 'GET',
                redirect: 'follow',
                mode: 'cors',
                headers: myHeaders
            };

            fetch(baseURL + "/api/auth/token", requestOptions)
            .then(function(response) {
                if(response.status === 200) {
                    response.json().then(function(data) {
                        duration = data.duration;
                        token = data.token;
                        // If successful, store token and duration in the session
                        sessionStorage.setItem('duration', duration);
                        sessionStorage.setItem('token', token);
                    }).then(location.href="./submit");
                }
            }).catch(err => {
                alert("Invalid credentials");
            });
        });
    });