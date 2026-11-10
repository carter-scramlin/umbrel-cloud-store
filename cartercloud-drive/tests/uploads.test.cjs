// SPDX-License-Identifier: AGPL-3.0-or-later
// Exercise the shipped uploader with network faults; server interoperability is in chunk_upload.py.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {sendFile}=require('../server/umbreldrive/js/fast.js');
const destination='https://drive.test/remote.php/dav/files/user/test.bin';
function fixture(size=9*1024*1024) {
 const blob=new Blob([new Uint8Array(size)]);blob.lastModified=1000000;
 const calls=[],progress=[];
 const client={uploadRoot:'https://drive.test/remote.php/dav/uploads/',uid:'user',uuid:()=> 'fixed',progress:(...args)=>progress.push(args),request:async(url,options)=>{calls.push({url,...options});return {ok:true};}};
 return {blob,calls,client,progress,controller:new AbortController()};
}
test('chunk boundaries, publication and no-overwrite policy',async()=>{
 const f=fixture();await sendFile(f.blob,destination,f.controller.signal,f.client);
 assert.deepEqual(f.calls.map(c=>c.method),['MKCOL','PUT','PUT','MOVE']);
 assert.deepEqual(f.calls.filter(c=>c.method==='PUT').map(c=>c.body.size),[8*1024*1024,1024*1024]);
 assert.equal(f.calls.at(-1).headers.Overwrite,'F');
 assert.equal(f.calls.at(-1).headers['OC-Total-Length'],String(f.blob.size));
 assert.ok(f.calls.every(c=>c.headers.Destination===destination));
});
test('lost chunk response retries the same chunk, final publication occurs once',async()=>{
 const f=fixture();const record=f.client.request;let failed=false;
 f.client.request=async(url,options)=>{await record(url,options);if(options.method==='PUT'&&!failed){failed=true;throw Error('Connection interrupted. Simulated');}};
 await sendFile(f.blob,destination,f.controller.signal,f.client);
 const puts=f.calls.filter(c=>c.method==='PUT');assert.equal(puts[0].url,puts[1].url);
 assert.equal(f.calls.filter(c=>c.method==='MOVE').length,1);
});
test('cancellation cleans the private session and never publishes partial content',async()=>{
 const f=fixture();const record=f.client.request;
 f.client.request=async(url,options)=>{await record(url,options);if(options.method==='PUT')f.controller.abort();};
 await assert.rejects(sendFile(f.blob,destination,f.controller.signal,f.client),{name:'AbortError'});
 assert.equal(f.calls.filter(c=>c.method==='MOVE').length,0);
 assert.equal(f.calls.at(-1).method,'DELETE');
});
test('a lost final response is not retried as another publication',async()=>{
 const f=fixture();const record=f.client.request;
 f.client.request=async(url,options)=>{await record(url,options);if(options.method==='MOVE')throw Error('Connection interrupted. Simulated');};
 await assert.rejects(sendFile(f.blob,destination,f.controller.signal,f.client));
 assert.equal(f.calls.filter(c=>c.method==='MOVE').length,1);
 assert.equal(f.calls.at(-1).method,'DELETE');
});
test('small uploads never overwrite; oversized uploads allocate no session',async()=>{
 const f=fixture(17);await sendFile(f.blob,destination,f.controller.signal,f.client);
 assert.equal(f.calls.length,1);assert.equal(f.calls[0].headers['If-None-Match'],'*');
 f.calls.length=0;
 await assert.rejects(sendFile({size:16*1024**3+1},destination,f.controller.signal,f.client),/16 GiB/);
 assert.equal(f.calls.length,0);
});
