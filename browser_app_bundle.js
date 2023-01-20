// this file needs to be browserified
// $ browserify browser_app_bundle.js -o ./public/js/app.js
// This will bundle all of the necessary dependencies
const Muse = require('muse-js') 
const request = require('request');
const url = require('url');

// The token is stored in a meta field in the layout.jade view
//console.log('csrf token: ' + document.querySelector('meta[name="token"]').content);

const BLINK_THRESHOLD = 95;
let recording = false;
var data = {"start_ts": null, "end_ts": null, "metadata": null, "eeg": [[], [], [], []], "ppg": [], "accel": []};

const DATA_URL = url.resolve(document.location.href, '/data');
//console.log(DATA_URL);

let CalculateRMS = function (arr) {
  // calculate the root mean sum-of-squares of an array
  let sum_squares = arr.map((val) => (val * val)).reduce((acum, val) => (acum + val));
  return Math.sqrt(sum_squares / arr.length);
}

async function main() {
  const graphTitles = [1, 2, 3, 4].map((x) => document.getElementById('electrode-name' + x));
  const rmsFields = [1, 2, 3, 4].map((x) => document.getElementById('rms' + x));
  const canvases = [1, 2, 3, 4].map((x) => document.getElementById('electrode' + x));
  const canvasCtx = canvases.map((canvas) => canvas.getContext('2d'));

  graphTitles.forEach((item, index) => {item.textContent = Muse.channelNames[index];});

  // Simple function to take the average of an array
  const average = arr => arr.reduce( ( p, c ) => p + c, 0 ) / arr.length;
  // for each 12-element eegReading array, adjust the appropriate canvas with a simple plot
  function plot(reading) {
    const canvas = canvases[reading.electrode];
    const context = canvasCtx[reading.electrode];
    if (!context) {
      return;
    }
    const width = canvas.width / 12.0;
    const height = canvas.height / 2.0;
    var color = "#4f837f"
    if (recording) {
      color = "#CDADFF"
    }
    context.fillStyle = color;
    context.clearRect(0, 0, canvas.width, canvas.height);
  
    // loop through each eeg reading (12 per array) and create a rectangle to visualize the voltage
    for (let i = 0; i < reading.samples.length; i++) {
      const sample = reading.samples[i] / 10.;
      if (sample > 0) {
        context.fillRect(i * 25, height - sample, width, sample);
      } else {
        context.fillRect(i * 25, height, width, -sample);
      }
    }
  }

  // initiate the web-bluetooth conection request
  let client = new Muse.MuseClient();
  client.enableAux = false;
  client.enablePpg = true;
  client.connectionStatus.subscribe((status) => {
    console.log(status ? 'Connected!' : 'Disconnected');
  });
  await client.connect();
  await client.start();
  document.getElementById("headset-name").innerText = client.deviceName;
  //document.getElementById('record_button').disabled = false;

  var last_frame = 0.0;
  const iter_update = 20;
  var mean_fr = 0.0;
  var iter = 0;

  client.eegReadings.subscribe(reading => {
    rmsFields[reading.electrode].textContent = CalculateRMS(reading.samples).toFixed(1)
    if (reading.electrode === 1) {
      // Update blink status
      if (Math.max.apply(null, reading.samples) >= BLINK_THRESHOLD) {
        document.getElementById('blinkStatus').innerText = "(>*.*)> Blink";
      } else {
        document.getElementById('blinkStatus').innerText = "(>o.o)> Eyes Open";
      }
      // compute EEG frame rate
      const fr = 1000 / (window.performance.now() - last_frame);
      if (isFinite(fr)) {
          mean_fr += fr;
          iter++;
      }
      if (iter % iter_update == 0) {
          document.getElementById('framerate').innerText = (mean_fr / iter_update).toFixed(1) + ' fps';
          iter = 0;
          mean_fr = 0;
      }
      last_frame = window.performance.now();
    }
    plot(reading);
    if (recording) {
      data['eeg'][reading.electrode].push(reading);
    }
  });
  client.telemetryData.subscribe((reading) => {
      //document.getElementById('temperature').innerText = reading.temperature.toString() + '℃';
      document.getElementById('batteryLevel').innerText = reading.batteryLevel.toFixed(2) + '%';
  });
  await client.deviceInfo().then((deviceInfo) => {
      //document.getElementById('hardware-version').innerText = deviceInfo.hw;
      //document.getElementById('firmware-version').innerText = deviceInfo.fw;
      data.metadata = deviceInfo;
      data.metadata.userid = document.querySelector('meta[name="userid"]').content;
      data.metadata.username = document.querySelector('meta[name="username"]').content;
  });
  client.accelerometerData.subscribe((accel) => {
      document.getElementById('acc-x').innerText = accel.samples[2].x.toFixed(3);
      document.getElementById('acc-y').innerText = accel.samples[2].y.toFixed(3);
      document.getElementById('acc-z').innerText = accel.samples[2].z.toFixed(3);
      if(recording) {
        data['accel'].push(accel);
      }
  });
  client.ppgReadings.subscribe((ppgreading) => {
      //document.getElementById('ppg' + ppgreading.ppgChannel).innerText = average(ppgreading.samples).toFixed(0);
      if(recording) {
        data['ppg'].push(ppgreading);
      }
  });
}

window.toggle_record = function () {
  const button = document.getElementById('record_button');
  if(recording) {
    console.log("stopping recording");
    document.getElementById('status').innerText = "Recording stopped";
    recording = false;
    button.innerText = "Start Recording";
    //button.style.backgroundColor = "#232";
    data.end_ts = Date.now();
    request({
	    url: DATA_URL,
	    method: "POST",
	    body: {_csrf: document.querySelector('meta[name="token"]').content},
	    json: data, 
	    headers: {'X-CSRF-Token': document.querySelector('meta[name="token"]').content}
	    },
      function (error, response, body) {
        if (!error && response.statusCode === 200) {
          console.log(body);
	  document.getElementById('status').innerText = "Data saved to server";
	} else {
          console.log("error: " + error);
          document.getElementById('status').innerText = "ERROR: Data not saved (" + error + ")";
        }
      });
    data = {"start_ts": null, "end_ts": null, "metadata": data.metadata, "eeg": [[], [], [], []], "ppg": [], "accel": []}; 
  } else {
    console.log("starting recording");
    document.getElementById('status').innerText = "Recording";
    recording = true;
    button.innerText = "Stop Recording";
    //button.style.backgroundColor = "#A23";
    data['start_ts'] = Date.now();
  }
}


// web-bluetooth can only be started by a user gesture.
// This funciton is called by an html button
window.connect = function () {
  main();
}

