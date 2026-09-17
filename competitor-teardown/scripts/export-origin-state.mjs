#!/usr/bin/env node
import { writeFile, rm } from 'node:fs/promises';

// Export one authorized tab, never the browser's entire cookie store.
const [endpoint, pageUrl, output] = process.argv.slice(2);
if (!endpoint || !pageUrl || !output) {
  console.error('Usage: node export-origin-state.mjs <loopback-CDP-websocket> <exact-tab-url> <new-state-file>');
  process.exit(2);
}
const remote = new URL(endpoint);
const page = new URL(pageUrl);
if (!['ws:', 'wss:'].includes(remote.protocol) || !['localhost', '127.0.0.1', '[::1]'].includes(remote.hostname)) {
  throw new Error('Use a loopback CDP websocket endpoint.');
}
if (!['http:', 'https:'].includes(page.protocol)) throw new Error('Expected an HTTP(S) page URL.');
const socket = new WebSocket(endpoint);
let sequence = 0;
const pending = new Map();
let sessionId;
let wrote = false;
function call(method, params = {}, session) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`${method} timed out`)); }, 15000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params, ...(session ? { sessionId: session } : {}) }));
  });
}
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  const request = pending.get(message.id);
  if (!request) return;
  pending.delete(message.id);
  clearTimeout(request.timer);
  if (message.error) request.reject(new Error('CDP command failed; no response data logged.'));
  else request.resolve(message.result);
});
socket.addEventListener('close', () => {
  for (const request of pending.values()) {
    clearTimeout(request.timer);
    request.reject(new Error('CDP connection closed.'));
  }
  pending.clear();
});
try {
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Chrome connection timed out; check its approval prompt.')), 45000);
    socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Cannot connect to Chrome.')); }, { once: true });
  });
  const { targetInfos } = await call('Target.getTargets');
  const matches = targetInfos.filter(t => t.type === 'page' && t.url === page.href);
  if (matches.length !== 1) throw new Error(`Expected one exact URL match, found ${matches.length}. Select a unique authorized tab.`);
  ({ sessionId } = await call('Target.attachToTarget', { targetId: matches[0].targetId, flatten: true }));
  const { result, exceptionDetails } = await call('Runtime.evaluate', {
    expression: `(() => { if (location.href !== ${JSON.stringify(page.href)}) throw new Error('Tab navigated'); const pairs = s => Object.entries(s).map(([name,value]) => ({name,value})); return {origin:location.origin,localStorage:pairs(localStorage),sessionStorage:pairs(sessionStorage)}; })()`,
    returnByValue: true,
  }, sessionId);
  if (exceptionDetails || result.value?.origin !== page.origin) throw new Error('Origin storage could not be read safely.');
  const { cookies } = await call('Network.getCookies', { urls: [page.href, page.origin + '/'] }, sessionId);
  const scoped = cookies.filter(cookie => {
    const domain = cookie.domain.replace(/^\./, '');
    return page.hostname === domain || (cookie.domain.startsWith('.') && page.hostname.endsWith('.' + domain));
  });
  await writeFile(output, JSON.stringify({ cookies: scoped, origins: [result.value] }), { flag: 'wx', mode: 0o600 });
  wrote = true;
  console.log(JSON.stringify({ origin: page.origin, cookies: scoped.length, localStorageEntries: result.value.localStorage.length, sessionStorageEntries: result.value.sessionStorage.length, stateFile: output }));
} catch (error) {
  if (wrote) await rm(output, { force: true });
  console.error(error.message);
  process.exitCode = 1;
} finally {
  if (sessionId && socket.readyState === WebSocket.OPEN) {
    await call('Target.detachFromTarget', { sessionId }).catch(() => {});
  }
  socket.close();
}
