const Muse = require('muse-js') // this node.js style import needs to be browserified
// $ browserify browser_app_bundle.js -o ./public/js/app.js
// This will bundle all of the necessary dependencies

const BLINK_THRESHOLD = 95;

let CalculateRMS = function (arr) {
  // calculate the root mean squared of an array
  let Squares = arr.map((val) => (val * val));
  let Sum = Squares.reduce((acum, val) => (acum + val));

  Mean = Sum / arr.length;
  return Math.sqrt(Mean);
}

async function main() {
  const graphTitles = [1, 2, 3, 4].map((x) => document.getElementById('electrode-name' + x));
  const rmsFields = [1, 2, 3, 4].map((x) => document.getElementById('rms' + x));
  const canvases = [1, 2, 3, 4].map((x) => document.getElementById('electrode' + x));
  const canvasCtx = canvases.map((canvas) => canvas.getContext('2d'));

  graphTitles.forEach((item, index) => {item.textContent = Muse.channelNames[index];});

  // Simple function to take the average of an array
  const average = arr => arr.reduce( ( p, c ) => p + c, 0 ) / arr.length;
  // for each 15 element array returned by the eegReading, adjust the appropriate canvas with a 
  // histogram like plot
  function plot(reading) {
    // identify the appropriate plot for the current electrode reading
    const canvas = canvases[reading.electrode];
    const context = canvasCtx[reading.electrode];
  
    // escape the function if the electrode is invalid
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
  
    // loop through each eeg reading (15 per array) and create a rectangle cooresponding
    // to the appropriate voltage
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
  client.connectionStatus.subscribe((status) => {console.log(status ? 'Connected!' : 'Disconnected');});
  await client.connect();
  await client.start();
  document.getElementById("headset-name").innerText = client.deviceName;

  var last_frame = 0.0;
  const iter_update = 20;
  var mean_fr = 0.0;
  var iter = 0;

  client.eegReadings.subscribe(reading => {
    rmsFields[reading.electrode].textContent = CalculateRMS(reading.samples).toString()
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
    if (recording === true) {
      storedResults[reading.electrode].push(CalculateRMS(reading.samples));
    }
  });

  client.telemetryData.subscribe((reading) => {
      document.getElementById('temperature').innerText = reading.temperature.toString() + '℃';
      document.getElementById('batteryLevel').innerText = reading.batteryLevel.toFixed(2) + '%';
  });
  await client.deviceInfo().then((deviceInfo) => {
      document.getElementById('hardware-version').innerText = deviceInfo.hw;
      document.getElementById('firmware-version').innerText = deviceInfo.fw;
  });
  client.accelerometerData.subscribe((accel) => {
      document.getElementById('acc-x').innerText = accel.samples[2].x.toFixed(3);
      document.getElementById('acc-y').innerText = accel.samples[2].y.toFixed(3);
      document.getElementById('acc-z').innerText = accel.samples[2].z.toFixed(3);
  });
  client.ppgReadings.subscribe((ppgreading) => {
      //console.log(ppgreading);
      document.getElementById('ppg' + ppgreading.ppgChannel).innerText = average(ppgreading.samples).toFixed(0);

  });
}

window.record = function () {
  recording = true
}

window.stop = function () {
  recording = false
}


// web-bluetooth can only be started by a user gesture.
// This funciton is called by an html button
window.connect = function () {
  main();
}

let recording = false;
var storedResults = [[], [], [], []]

