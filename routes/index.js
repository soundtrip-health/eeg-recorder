var express = require('express');
var ensureLogIn = require('connect-ensure-login').ensureLoggedIn;
var db = require('../db');

let CalculateRMS = function (arr) {

  // calculate the root mean squared of an array

  let Squares = arr.map((val) => (val * val));
  let Sum = Squares.reduce((acum, val) => (acum + val));

  Mean = Sum / arr.length;
  return Math.sqrt(Mean);
}

var router = express.Router();

var ensureLoggedIn = ensureLogIn();

/* GET home page. */
router.get('/', function(req, res, next) {
  console.log("req.user: ");
  console.dir(req.user);
  if (!req.user) 
    return res.render('login');
  console.log(req.user);
  res.render('index', {user: req.user.name, title: "Home", num_headsets: 3});
});

module.exports = router;
