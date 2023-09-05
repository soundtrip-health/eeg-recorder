# eeg-recorder
Simple bluetooth EEG Recorder app for Muse EEG headband devices. All the hard work is done by [muse-js](https://github.com/urish/muse-js). 

## Running the server 

Be sure to create user credentials in a users.csv file at the top level (see users_example.csv for an example of the format). Then you can run a local instance of the web app with:

```bash
browserify browser_app_bundle.js -o public/js/app.js
npm start
```
The server should now be running at [http://localhost:3000](http://localhost:3000). Of course, for a real deplyment, you will want to run this behind a secure proxy (e.g., nginx).

## Contributing

THe main webapp client code is in browser_app_bundle.js. If you edit this, be sure to rebuild the client-side bundle with: 

```
browserify browser_app_bundle.js -o public/js/app.js
```

The server-side logic for the (very simple) api is in routes/index.js. This defines a simple static server to deliver the webapp static content and several REST endpoints with which the client-side javascript code interacts.

## Data Analysis
Analysis code is a work-in-progress. There are some very rough examples for loading and visualizing data in analysis/eeg.ipynb. 

