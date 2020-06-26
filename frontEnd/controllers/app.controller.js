const baseURLEnv = process.env.baseURL;

// Controller for the login page
exports.login = function (req, res) {
	res.render("login", {
        baseURL : process.env.baseURL
    });
};

// Controller for submit
exports.submit = function(req,res) {
    res.render("submit", {
        baseURL : process.env.baseURL
    });
};

// Controller for update
exports.update = function(req,res) {
    res.render("update", {
        baseURL : process.env.baseURL
    });
};