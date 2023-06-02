// import Guacamole from "guacamole-common-js";


// Get query parameters
import Guacamole from "guacamole-common-js";

const queryParams = getQueryParams();
const sessionToken = queryParams['sessionToken'];
const transmissionKey = queryParams['transmissionKey'];
const recordUid = queryParams['recordUid'];
const gatewayUid = queryParams['gatewayUid'];


console.log("queryParams: [" + queryParams + "]");
console.log("sessionToken: [" + sessionToken + "]");
console.log("transmissionKey: [" + transmissionKey + "]");
console.log("recordUid: [" + recordUid + "]");
console.log("gatewayUid: [" + gatewayUid + "]")


// Construct the tunnelUrl
const tunnelUrl = "wss://localhost:5001/client?Authorization=KeeperUser%20" + sessionToken + "&TransmissionKey=" + transmissionKey + "&RecordUid=" + recordUid + "key=" + "RECORD_KEY";

const guac = new Guacamole.Client(new Guacamole.WebSocketTunnel(tunnelUrl));

// Get the display div element
const display = document.getElementById('display');
display.appendChild(guac.getDisplay().getElement());

// Connect to the Guacamole server
guac.connect();

// Add keyboard event listeners
const keyboard = new Guacamole.Keyboard(document);
keyboard.onkeydown = function (keysym) {
    guac.sendKeyEvent(1, keysym);
};
keyboard.onkeyup = function (keysym) {
    guac.sendKeyEvent(0, keysym);
};

// Handle disconnection
guac.onerror = function (error) {
    console.error('Guacamole error:', error);
    guac.disconnect();
};

window.onunload = function () {
    guac.disconnect();
};


// Function to parse query parameters
function getQueryParams() {
    const queryParams = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');

    for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i].split('=');
        queryParams[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
    }

    return queryParams;
}
