const Muse = require('muse-js') // this node.js style import needs to be browserified
// $ browserify browser_app_bundle.js -o ./public/js/app.js
// This will bundle all of the necessary dependencies

const graphTitles = Array.from(document.querySelectorAll('.electrode-item h4'));

// hook onto and store the cavas div/ canvas context
const canvases = Array.from(document.querySelectorAll('.electrode-item canvas'));
const canvasCtx = canvases.map((canvas) => canvas.getContext('2d'));
const blinkStatus = document.querySelector('#blinkStatus');

var recording = false

var storedResults = [
  [],
  [],
  [],
  []
]

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

let CalculateRMS = function (arr) {

  // calculate the root mean squared of an array

  let Squares = arr.map((val) => (val * val));
  let Sum = Squares.reduce((acum, val) => (acum + val));

  Mean = Sum / arr.length;
  return Math.sqrt(Mean);
}

async function main() {
  // initiate the web-bluetooth conection request
  let client = new Muse.MuseClient();
  await client.connect();
  await client.start();

  client.eegReadings.subscribe(reading => {
    plot(reading);
    graphTitles[reading.electrode].textContent = CalculateRMS(reading.samples).toString()
    if (reading.electrode === 0) {
      if (Math.max.apply(null, reading.samples) >= 95) {
        blinkStatus.textContent = "(>*.*)> Blink";
      } else {
        blinkStatus.textContent = "(>o.o)> Eyes Open";
      }
    }
    if (recording === true) {
      // storedResults[reading.electrode].push(Math.abs(Math.max.apply(null, reading.samples)));
      storedResults[reading.electrode].push(CalculateRMS(reading.samples));
    }
  });

  client.accelerometerData.subscribe(acceleration => {
    console.log(acceleration);
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

