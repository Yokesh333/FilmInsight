const fs = require('fs');
const http = require('http');

const chatflowFile = '/app/500DaysofSummer Chatflow.json';
if (!fs.existsSync(chatflowFile)) {
  console.error(`Chatflow file not found at ${chatflowFile}`);
  process.exit(1);
}

const chatflowData = JSON.parse(fs.readFileSync(chatflowFile, 'utf8'));
const payload = JSON.stringify({
  name: "500 Days of Summer Chatflow",
  flowData: JSON.stringify(chatflowData),
  deployed: true,
  isPublic: true,
  type: "CHATFLOW"
});

// Function to wait for Flowise to start
function waitForFlowise(retries = 30, delay = 2000) {
  return new Promise((resolve, reject) => {
    const check = (attempt) => {
      console.log(`Checking if Flowise is ready (attempt ${attempt}/${retries})...`);
      const req = http.get('http://localhost:3000/api/v1/ping', (res) => {
        if (res.statusCode === 200) {
          console.log('Flowise is ready!');
          resolve();
        } else {
          retry(attempt);
        }
      });
      req.on('error', () => retry(attempt));
      req.end();
    };

    const retry = (attempt) => {
      if (attempt >= retries) {
        reject(new Error('Flowise failed to start in time.'));
      } else {
        setTimeout(() => check(attempt + 1), delay);
      }
    };

    check(1);
  });
}

async function importChatflow() {
  try {
    await waitForFlowise();

    // Check if chatflow already exists to prevent duplicate imports
    console.log('Checking existing chatflows...');
    const existingChatflows = await new Promise((resolve, reject) => {
      const req = http.get('http://localhost:3000/api/v1/chatflows', (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(data));
          } else {
            reject(new Error(`Failed to get chatflows: Status ${res.statusCode}`));
          }
        });
      });
      req.on('error', reject);
      req.end();
    });

    const exists = existingChatflows.some(cf => cf.name === "500 Days of Summer Chatflow");
    if (exists) {
      console.log('Chatflow "500 Days of Summer Chatflow" already exists. Skipping import.');
      return;
    }

    console.log('Importing "500 Days of Summer Chatflow"...');
    await new Promise((resolve, reject) => {
      const options = {
        hostname: 'localhost',
        port: 3000,
        path: '/api/v1/chatflows',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload)
        }
      };

      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          if (res.statusCode === 200 || res.statusCode === 201) {
            console.log('Chatflow successfully imported!');
            resolve();
          } else {
            reject(new Error(`Failed to import chatflow: Status ${res.statusCode} - ${data}`));
          }
        });
      });

      req.on('error', reject);
      req.write(payload);
      req.end();
    });

  } catch (error) {
    console.error('Error importing chatflow:', error.message);
  }
}

importChatflow();
