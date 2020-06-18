    $(document).ready(function() {
        $('#loginbtn').click(function(e) {
            e.preventDefault();
            var credentials = $('#login').serializeArray();
            var username = credentials[0].value;
            var password = credentials[1].value;
            var duration;
            var token;

            var myHeaders = new Headers();
            var to_encode = username+":"+password;
            var base64_encoded = btoa(to_encode);
            myHeaders.append("Authorization", "Basic "+base64_encoded);
            myHeaders.append("Access-Control-Allow-Origin", "*");

            var requestOptions = {
                // mode: 'no-cors',
                method: 'GET',
                headers: myHeaders,
                redirect: 'follow'
            };

            fetch(baseURL + "/api/auth/token", requestOptions)
            .then(function(response) {
                if(response.status === 200) {
                    response.json().then(function(data) {
                        duration = data.duration;
                        token = data.token;
                        sessionStorage.setItem('duration', duration);
                        sessionStorage.setItem('token', token);
                    }).then(location.href="./submit");
                }
            }).catch(err => {
                alert("Invalid credentials");
            });
        });
    });