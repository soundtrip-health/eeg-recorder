const express = require('express');
const ensureLogIn = require('connect-ensure-login').ensureLoggedIn;
const db = require('../db');
const fs = require('fs');
const path = require('node:path');

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
// curl -X POST http://localhost:3000/data -H 'Content-Type: application/json' -d '{"foo":1, "bar":"two"}'
router.post('/data', ensureLoggedIn, function(req, res, next) { 
  const user_dir = path.join(db.data_dir, req.user.username);
  try {
    fs.mkdirSync(user_dir, {recursive: true});
  } catch(err) {
    console.error('Failed to create data dir: ' + user_dir + '. Error: ' + err);
    //console.log(err);
  }
  let d = new Date(req.body.data.start_ts);
  const filename = path.join(user_dir, req.body.device + '_' + d.toISOString() + '.json')
  fs.writeFile(filename, JSON.stringify(req.body.data), 'utf8', err => {
    if (err) {
      console.error('Failed to save data to ' + filename + '. Error: ' + err);
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

router.get('/data', ensureLoggedIn, function(req, res, next) {
  const user_dir = path.join(db.data_dir, req.user.username);
  fs.readdir(user_dir, (err, files) => {
    if (!files) files = [];
    files = files.filter(fn => fn.endsWith('.json'));
    //console.dir(files);
    res.render('data', {user: req.user, title: "Data", files: files});
  });
});

router.get('/data/:id', ensureLoggedIn, function(req, res, next) {
  const user_dir = path.join(db.data_dir, req.user.username);
  //res.send('id: ' + req.params.id);
  file = user_dir + '/' + req.params.id;
  console.log('Downloading ' + file);
  res.download(file);
});


module.exports = router;
