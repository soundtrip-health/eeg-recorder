var express = require('express');
var ensureLogIn = require('connect-ensure-login').ensureLoggedIn;
var db = require('../db');

var router = express.Router();

var ensureLoggedIn = ensureLogIn();

/* GET home page. */
router.get('/', function(req, res, next) {
  if (!req.user) 
    return res.render('login');
  console.log(req.user);
  res.render('index', {user: req.user.id, title: "Home"});
});

module.exports = router;
