const createError = require('http-errors');
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const csrf = require('csurf');
const passport = require('passport');
const logger = require('morgan');

// The maximimum json payload size. This must be large enough to handle all anticipated data uploads.
const JSON_PAYLOAD_MAX = "100mb";

// pass the session to the connect sqlite3 module
// allowing it to inherit from session.Store
const SQLiteStore = require('connect-sqlite3')(session);

const indexRouter = require('./routes/index');
const authRouter = require('./routes/auth');

var app = express();
app.use(bodyParser.urlencoded({limit: JSON_PAYLOAD_MAX, extended: true}));
app.use(bodyParser.json({limit: JSON_PAYLOAD_MAX, extended: true}))

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'pug');

app.use(logger('dev'));
app.use('/favicon.ico', express.static('public/images/favicon.ico'));
app.use(express.json({limit: JSON_PAYLOAD_MAX, extended: true}));
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
  secret: 'white rabbit',
  resave: false, // don't save session if unmodified
  saveUninitialized: false, // don't create session until something stored
  store: new SQLiteStore({ db: 'sessions.db', dir: './var/db' })
}));
app.use(csrf());
app.use(passport.authenticate('session'));
app.use(function(req, res, next) {
  var msgs = req.session.messages || [];
  res.locals.messages = msgs;
  res.locals.hasMessages = !! msgs.length;
  req.session.messages = [];
  next();
});
app.use(function(req, res, next) {
  res.locals.csrfToken = req.csrfToken();
  next();
});


app.use('/', indexRouter);
app.use('/', authRouter);


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
