// Rendert jede *.html in diesem Ordner mit headless Chrome (CDP Page.printToPDF) nach pdf/<name>.pdf.
// Aufruf: node vorlagen/dokumente/build-pdfs.mjs [name ...]   (ohne Namen: alle)
import { spawn } from 'node:child_process';
import { readdirSync, writeFileSync, mkdirSync, renameSync } from 'node:fs';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9335;
const PROFIL = '/private/tmp/claude-503/cdp-pdf';
const HIER = dirname(fileURLToPath(import.meta.url));
const ZIEL = join(HIER, 'pdf');

const gewuenscht = process.argv.slice(2);
const dateien = readdirSync(HIER)
  .filter(f => f.endsWith('.html'))
  .filter(f => !gewuenscht.length || gewuenscht.includes(basename(f, '.html')));
if (!dateien.length) { console.error('Keine HTML-Dateien gefunden.'); process.exit(1); }
mkdirSync(ZIEL, { recursive: true });

const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${PROFIL}`, '--no-first-run', '--allow-file-access-from-files', 'about:blank'], { stdio: 'ignore' });
const beenden = () => { try { chrome.kill(); } catch {} };
process.on('exit', beenden);

async function verbinden() {
  for (let i = 0; i < 50; i++) {
    try {
      const t = await (await fetch(`http://127.0.0.1:${PORT}/json`, { signal: AbortSignal.timeout(1000) })).json();
      const seite = t.find(x => x.type === 'page');
      if (seite) return seite.webSocketDebuggerUrl;
    } catch {}
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error(`Chrome antwortet nicht auf Port ${PORT}`);
}

const ws = new WebSocket(await verbinden());
await new Promise((r, f) => { ws.onopen = r; ws.onerror = f; });
let id = 0; const offen = new Map(); const ereignisse = [];
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id && offen.has(m.id)) { const { r, f } = offen.get(m.id); offen.delete(m.id); m.error ? f(new Error(m.error.message)) : r(m.result); }
  else if (m.method) ereignisse.forEach(h => h(m));
};
const send = (method, params = {}, ms = 60000) => new Promise((r, f) => {
  const i = ++id; offen.set(i, { r, f }); ws.send(JSON.stringify({ id: i, method, params }));
  setTimeout(() => { if (offen.has(i)) { offen.delete(i); f(new Error(`${method}: Timeout`)); } }, ms);
});
const warteAuf = (name, ms = 30000) => new Promise((r, f) => {
  const h = m => { if (m.method === name) { ereignisse.splice(ereignisse.indexOf(h), 1); r(m.params); } };
  ereignisse.push(h); setTimeout(() => f(new Error(`${name}: Timeout`)), ms);
});

await send('Page.enable');
await send('Network.enable');
// Google Fonts liefert Chrome variable Schriften (Archivo, Plex Sans). Die bettet Chrome nur als
// Type-3-Konturen ohne Namen ins PDF ein. Mit neutralem User-Agent kommen statische TTF-Schnitte,
// die als echte TrueType-Schriften (IBMPlexSans-Bold, Archivo-Black …) eingebettet werden.
await send('Network.setUserAgentOverride', { userAgent: 'Mozilla/5.0 (msb-dokumente)' });
await send('Network.setCacheDisabled', { cacheDisabled: true });
let fehler = 0;
for (const f of dateien) {
  const name = basename(f, '.html');
  const geladen = warteAuf('Page.loadEventFired');
  await send('Page.navigate', { url: pathToFileURL(join(HIER, f)).href });
  await geladen;
  // Erst drucken, wenn die Webfonts wirklich da sind; sonst bettet Chrome einen Ersatz ein.
  const { result } = await send('Runtime.evaluate', { awaitPromise: true, returnByValue: true, expression: `(async () => {
    await document.fonts.ready;
    const noetig = ['900 30pt Archivo', '800 18pt Archivo', '400 10pt "IBM Plex Sans"', '700 10pt "IBM Plex Sans"', '400 8pt "IBM Plex Mono"', '500 8pt "IBM Plex Mono"'];
    await Promise.all(noetig.map(s => document.fonts.load(s, 'Aa§ä')));
    const fehlt = noetig.filter(s => !document.fonts.check(s, 'Aa§ä'));
    const bilder = [...document.images].every(i => i.complete && i.naturalWidth > 0);
    return { fehlt, bilder };
  })()` });
  const pruef = result.value;
  if (pruef.fehlt.length || !pruef.bilder) {
    console.error(`✗ ${name}: Schriften fehlen ${JSON.stringify(pruef.fehlt)}, Bilder ok: ${pruef.bilder}`);
    fehler++; continue;
  }
  const { data } = await send('Page.printToPDF', {
    preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false,
    marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0,
  });
  const ziel = join(ZIEL, `${name}.pdf`);
  writeFileSync(ziel + '.tmp', Buffer.from(data, 'base64'));
  renameSync(ziel + '.tmp', ziel);
  console.log(`✓ pdf/${name}.pdf`);
}
ws.close(); beenden();
process.exit(fehler ? 1 : 0);
