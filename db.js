const sqlite3 = require('sqlite3');
const mkdirp = require('mkdirp');
const crypto = require('crypto');
const fs = require('fs');

const csvToArray = (data) => {
  const re = /(,|\r?\n|\r|^)(?:"([^"]*(?:""[^"]*)*)"|([^,\r\n]*))/gi
  const result = [[]]
  let matches
  while ((matches = re.exec(data))) {
    if (matches[1].length && matches[1] !== ',') result.push([])
    result[result.length - 1].push(
      matches[2] !== undefined ? matches[2].replace(/""/g, '"') : matches[3]
    )
  }
  return result.slice(0, -1)
}

mkdirp.sync('./var/db');

var db = new sqlite3.Database('./var/db/eeg_recorder.db');

// create the database schema for the app
db.serialize(function() {
  db.run("CREATE TABLE IF NOT EXISTS users ( \
    id INTEGER PRIMARY KEY, \
    username TEXT UNIQUE, \
    hashed_password BLOB, \
    salt BLOB \
  )");
  
  db.run("CREATE TABLE IF NOT EXISTS metadata ( \
    id INTEGER PRIMARY KEY, \
    user_id INTEGER NOT NULL, \
    filename TEXT NOT NULL, \
    uploaded INTEGER \
  )");
  
  // default users to populate the users db
  // users.csv should be a comma-separated list of username,password
  // note that the password cannot contain csv-advers chars, like commas and quotes.
  var salt = crypto.randomBytes(16);
  try {
    const users = csvToArray(fs.readFileSync('users.csv', 'utf8'));
    users.forEach(user => {
      db.run('INSERT OR IGNORE INTO users (username, hashed_password, salt) VALUES (?, ?, ?)', 
             [user[0], crypto.pbkdf2Sync(user[1], salt, 310000, 32, 'sha256'), salt]);
    });
  } catch (err) {
    console.log(err);
    console.log("Maybe you forgot to create the users.csv file? (list of username,password)");
  }

});

module.exports = db;
