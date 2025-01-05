# eeg-recorder
Simple bluetooth EEG Recorder app for Muse EEG headband devices. All the hard work is done by [muse-js](https://github.com/urish/muse-js).

## Setup

The following is what I'm using in Ubuntu 24 LTS.

```bash
# Use nodesource nodejs/npm packages (ubuntu's can get quite out of date)
curl -sL https://deb.nodesource.com/setup_16.x -o /tmp/nodesource_setup.sh
# Inspect the script
cat /tmp/nodesource_setup.sh
# install
sudo bash /tmp/nodesource_setup.sh
sudo apt install nodejs 
# install browserify
sudo npm install -g browserify
# Install dependencies
cd ~/git/eeg-record
npm install
```

Note that you may see some "vulnerabilities" from the audit that npm install runs. The issues that I see are meaningless in the context of how the packages are used (to prepare a webapp). More info on the [npm audit issues](https://overreacted.io/npm-audit-broken-by-design/). BTW, the audit messages also often lye about a fix being availabale-- neither `npm audit fix` nor `npm audit fix --force` fixes the two vulnerabilities that it claims it can fix.

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

