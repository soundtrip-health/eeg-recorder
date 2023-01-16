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

// GET home page
router.get('/', ensureLoggedIn, function(req, res, next) {
  console.log("req.user: "); console.dir(req.user);
  if (!req.user) 
    return res.render('login');
  console.log(req.user);
  res.render('index', {user: req.user.username, title: "Home", num_headsets: 3});
});


// POST data
router.post('/', ensureLoggedIn, function(req, res, next) {
  req.body.title = req.body.title.trim();
  next();
}, function(req, res, next) {
  db.run('INSERT INTO data (user_id, filename, upload_ts) VALUES (?, ?, ?)', [
    req.user.id,
    req.body.filename,
    Math.round(Date.now() / 1000)
  ], function(err) {
    if (err) { return next(err); }
    return res.redirect('/');
  });
});

module.exports = router;
