import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '../..');

function loadEnv(envPath) {
  const vars = {};
  if (!existsSync(envPath)) return vars;
  const lines = readFileSync(envPath, 'utf-8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    vars[key] = val;
  }
  return vars;
}

const dotenv = loadEnv(resolve(ROOT, 'frontend/.env'));
const dotenvProd = loadEnv(resolve(ROOT, 'frontend/.env.production'));
const processEnv = process.env || {};

function env(key, fallback) {
  return dotenvProd[key] || dotenv[key] || processEnv[key] || fallback;
}

const firebaseJson = {
  hosting: {
    public: 'frontend/dist',
    ignore: ['firebase.json', '**/.*', '**/node_modules/**'],
    rewrites: [
      {
        source: '/api/**',
        run: {
          serviceId: env('HOSTING_SERVICE_ID', 'ecomentor-api'),
          region: env('HOSTING_REGION', 'us-central1'),
        },
      },
      {
        source: '**',
        destination: '/index.html',
      },
    ],
    headers: [
      {
        source: '**/*.@(js|css|svg|png|jpg|ico)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
        ],
      },
      {
        source: 'sw.js',
        headers: [
          { key: 'Cache-Control', value: 'no-cache' },
        ],
      },
    ],
  },
  firestore: {
    rules: 'backend/firestore.rules',
    indexes: 'backend/firestore.indexes.json',
  },
};

const outPath = resolve(ROOT, 'firebase.json');
writeFileSync(outPath, JSON.stringify(firebaseJson, null, 2) + '\n');
console.log(`Generated ${outPath}`);
console.log(`  serviceId: ${firebaseJson.hosting.rewrites[0].run.serviceId}`);
console.log(`  region: ${firebaseJson.hosting.rewrites[0].run.region}`);
