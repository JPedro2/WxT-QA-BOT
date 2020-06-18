// ------------------ NPM Dependency ------------------
const express = require("express");
const router = express.Router();

//Import the controller
const appController = require("../controllers/app.controller");


//Route : Home - send them to login. 
router.get('/', appController.login)

//Route : Login - send them to login.
router.get('/login', appController.login)

//Route: Main Page 
router.get('/submit', appController.submit)

//Route: Update
router.get('/update', appController.update)

module.exports = router;
