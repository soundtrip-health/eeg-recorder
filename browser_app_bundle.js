// this file needs to be browserified
// $ browserify browser_app_bundle.js -o ./public/js/app.js
// This will bundle all of the necessary dependencies
const Muse = require('muse-js') 
const request = require('request');
const url = require('url');

// The token is stored in a meta field in the layout.jade view
//console.log('csrf token: ' + document.querySelector('meta[name="token"]').content);
const DATA_URL = url.resolve(document.location.href, '/data');
const BLINK_THRESHOLD = 95;

const calculateRms = function (arr) {
  // calculate the root mean sum-of-squares of an array
  let sum_squares = arr.map((val) => (val * val)).reduce((acum, val) => (acum + val));
  return Math.sqrt(sum_squares / arr.length);
}

// Simple function to take the average of an array
const average = arr => arr.reduce((p, c) => p + c, 0) / arr.length;

const DATA_STRUCT = {"start_ts": null, 
                     "end_ts": null, 
	             "metadata": null, 
	             "eeg": [[], [], [], []], 
	             "ppg": [], 
	             "accel": [],
	             "gyro": []};

// recording is a global, as recording is triggered by one button for all devices
var recording = false;

const connectedDevices = [];

class EegDevice {
  constructor(divId) {
    this.deviceName = null;
    this.div = document.getElementById('headset-' + divId);
    this.graphTitles = [1, 2, 3, 4].map((x) => document.getElementById('electrode-name' + x + '-' + divId));
    this.rmsFields = [1, 2, 3, 4].map((x) => document.getElementById('rms' + x + '-' + divId));
    this.canvases = [1, 2, 3, 4].map((x) => document.getElementById('electrode' + x + '-' + divId));
    this.nameElem = document.getElementById('headset-name-' + divId);
    this.blinkStatElem = document.getElementById('blinkStatus-' + divId);
    this.frameRateElem = document.getElementById('framerate-' + divId);
    this.accelIds = ['x', 'y', 'z'].map((x) => document.getElementById('acc-' + x + '-' + divId));
    this.ppgIds = ['0', '1', '2'].map((x) => document.getElementById('ppg-' + x + '-' + divId));
    this.batteryElem = document.getElementById('batteryLevel-' + divId);  
    this.data = DATA_STRUCT;
  }

  hide() {
    this.div.style.display = 'block';
  }

  show() {
    this.div.style.display = 'block';
    this.graphTitles.forEach((item, index) => {item.textContent = Muse.channelNames[index];});
  }

  plot(reading) {
    const canvas = this.canvases[reading.electrode];
    const context = this.canvasCtx[reading.electrode];
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

  async connect() {
    this.canvasCtx = this.canvases.map((canvas) => canvas.getContext('2d'));
    // initiate the web-bluetooth conection request
    this.client = new Muse.MuseClient();
    this.client.enableAux = false;
    this.client.enablePpg = true;
    this.client.connectionStatus.subscribe((status) => {
      console.log(status ? 'Connected!' : 'Disconnected');
    });
    await this.client.connect();
    this.deviceName = this.client.deviceName;
  }

  disconnect() {
    this.client.disconnect();
  }

  async pause() {
    this.client.pause();
  }

  async resume() {
    this.client.resume();
  }

  async start() {
    this.nameElem.innerText = this.deviceName;
    await this.client.start();
    let last_frame = 0.0;
    const iter_update = 20;
    let mean_fr = 0.0;
    let iter = 0;
    this.client.eegReadings.subscribe(reading => {
      this.rmsFields[reading.electrode].textContent = calculateRms(reading.samples).toFixed(1)
      if (reading.electrode === 1) {
        // Update blink status
        if (Math.max.apply(null, reading.samples) >= BLINK_THRESHOLD) {
          this.blinkStatElem.innerText = "(>*.*)> Blink";
        } else {
          this.blinkStatElem.innerText = "(>o.o)> Eyes Open";
        }
        // compute EEG frame rate
        const fr = 1000 / (window.performance.now() - last_frame);
        if (isFinite(fr)) {
            mean_fr += fr;
            iter++;
        }
        if (iter % iter_update == 0) {
            this.frameRateElem.innerText = (mean_fr / iter_update).toFixed(1) + ' fps';
            iter = 0;
            mean_fr = 0;
        }
        last_frame = window.performance.now();
      }
      this.plot(reading);
      if (recording) {
        this.data['eeg'][reading.electrode].push(reading);
      }
    });
    this.client.telemetryData.subscribe((reading) => {
        //document.getElementById('temperature').innerText = reading.temperature.toString() + '℃';
        this.batteryElem.innerText = reading.batteryLevel.toFixed(2) + '%';
    });
    await this.client.deviceInfo().then((deviceInfo) => {
        this.data.metadata = deviceInfo;
        this.data.metadata.userid = document.querySelector('meta[name="userid"]').content;
        this.data.metadata.username = document.querySelector('meta[name="username"]').content;
        this.data.metadata.deviceName = this.client.deviceName;
	this.data.metadata.electrodeNames = Muse.channelNames;
    });
    this.client.accelerometerData.subscribe((accel) => {
      this.accelIds[0].innerText = accel.samples[2].x.toFixed(3);
      this.accelIds[1].innerText = accel.samples[2].y.toFixed(3);
      this.accelIds[2].innerText = accel.samples[2].z.toFixed(3);
      if(recording) {
        this.data['accel'].push(accel);
      }
    });
    this.client.gyroscopeData.subscribe((gyro) => {
      if(recording) {
        this.data['gyro'].push(gyro);
      }
    });
    this.client.ppgReadings.subscribe((ppgreading) => {
      if(recording) {
        this.data['ppg'].push(ppgreading);
      }
    });
  }

  upload_data() {
    request({
            url: DATA_URL,
            method: "POST",
	    json: {device: this.data.metadata.deviceName, data: this.data}
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
    this.data = DATA_STRUCT;
  }
}

window.toggle_record = function () {
  const button = document.getElementById('record_button');
  if(recording) {
    console.log("stopping recording");
    document.getElementById('status').innerText = "Recording stopped";
    recording = false;
    button.innerText = "Start Recording";
    //button.style.backgroundColor = "#232";
    connectedDevices.forEach((device) => {
      device.upload_data();
    });
  } else {
    console.log("starting recording");
    document.getElementById('status').innerText = "Recording";
    recording = true;
    button.innerText = "Stop Recording";
    //button.style.backgroundColor = "#A23";

    // FIXME: should use a setter
    connectedDevices.forEach(device => device.data['start_ts'] = Date.now());
  }
}


// web-bluetooth can only be started by a user gesture.
// This funciton is called by an html button
var nextDivId = 0;
window.connect = async function () {
  const device = new EegDevice(nextDivId);
  console.log('connecting...');
  
  try {
    await device.connect();
  } catch (e) {
    if (e instanceof DOMException) {
      console.log('User canceled connection request.');
      return;
    } else {
      throw e;
    }
  }

  if (connectedDevices.some(o => o.deviceName === device.deviceName)) {
    console.log('Device ' + device.name + ' is already connected.');
    window.alert('Device ' + device.name + ' is already connected.');
    //document.getElementById('status').innerText = 'ERROR: Device ' + device.name + ' already connected.';
  } else {
    nextDivId++;
    device.show();
    device.start();
    connectedDevices.push(device);
  }
}

