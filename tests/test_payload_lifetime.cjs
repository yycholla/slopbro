// Offline browser fixture: the Luna bridge is mocked; no TV or network calls.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../wwwroot/index.html'), 'utf8');
const script = source.match(/<script>([\s\S]*?)<\/script>/)[1];
function fixture(extra = '') {
  const nodes = new Map(), calls = [];
  function Bridge() { this.call = (...args) => calls.push(args); this.cancel = () => {}; }
  const context = {window: {}, PalmServiceBridge: Bridge,
    location: {search:'?script=autoroot.sh&files=package.json;main.js' + extra,pathname:'/index.html',origin:'http://fixture'},
    document: {getElementById(id) { if (!nodes.has(id)) nodes.set(id, {}); return nodes.get(id); }},
    Image: function () {}, console};
  vm.runInNewContext(script, context);
  return {context, calls, nodes};
}
const {context, calls} = fixture();
assert.ok(Array.isArray(context.window.__slopbroActiveBridges), 'pending Luna bridge needs a window-owned strong reference');
assert.equal(context.window.__slopbroActiveBridges.length, 1);
assert.equal(typeof context.window.__slopbroActiveBridges[0].onservicecallback, 'function');
assert.ok(calls[0][0].includes('/download'));
const staged = fixture('&staged-dir=/tmp/slopbro-stage-123456');
assert.equal(staged.calls.length, 1);
assert.equal(staged.calls[0][0], 'luna://com.webos.service.jsserver/run');
assert.ok(JSON.parse(staged.calls[0][1]).inputParams.includes('/tmp/slopbro-stage-123456/autoroot.sh'));
for (const invalid of ['/tmp/slopbro-stage-1;id', '/tmp/slopbro-stage-1/../other', '/media/internal/downloads', '']) {
  const bad = fixture('&staged-dir=' + encodeURIComponent(invalid));
  assert.equal(bad.calls.length, 0, 'invalid staging path must not invoke a Luna service');
  assert.match(bad.nodes.get('error').textContent, /invalid staged directory/);
}
console.log('Payload bridge lifetime and staged-directory fixtures passed');
