const express = require('express');
const ensureLogIn = require('connect-ensure-login').ensureLoggedIn;
const db = require('../db');
const fs = require('fs');
const path = require('node:path');

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
  if (!req.user) 
    return res.render('login');
  console.log(req.user);
  res.render('index', {user: req.user, title: "Home", num_headsets: 3});
});


// POST data
// TOKEN="dNNLFbGd-Ew_2I5H6hjamKRt0R8htlt7qE5Q"
// curl -X POST http://localhost:3000/data -H 'Content-Type: application/json' -H X-CSRF-Token: ${TOKEN}' -d '{"foo":1, "bar":"two"}'
router.post('/data', function(req, res, next) {
  //console.log(req.body);
  const user_dir = path.join(db.data_dir, req.user.username);
  try {
    fs.mkdirSync(user_dir, {recursive: true});
  } catch(err) {
    console.log(err);
  }
  const filename = path.join(user_dir, req.user.username + '_' + req.body.start_ts + '.json')
  fs.writeFile(filename, JSON.stringify(req.body), 'utf8', err => {
    if (err) {
      console.error(err);
    }
    console.log('file saved to ' + filename + '.');
  });
/*
  db.database.run('INSERT INTO data (user_id, data, upload_ts) VALUES (?, ?, ?)', [
    req.user.id,
    filename,
    Math.round(Date.now() / 1000)
  ], function(err) {
    if (err) { return next(err); }
    return res.redirect('/');
  });
*/
});

router.get('/data', function(req, res, next) {
  const user_dir = path.join(db.data_dir, req.user.username);
  fs.readdir(user_dir, (err, files) => {
    console.dir(files);
    res.render('data', {user: req.user, title: "Data", files: files});
  });
});
module.exports = router;
