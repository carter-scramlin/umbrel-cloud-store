/* SPDX-License-Identifier: AGPL-3.0-or-later */
// Opt-in, local-only diagnostic for comparing the full workspace. No telemetry.
(() => {
 if(document.getElementById('drive-performance'))return;
 const expected=new URL(location.href).searchParams.get('drivePerfName')||'';
 const out=document.createElement('output');out.id='drive-performance';
 Object.assign(out.style,{position:'fixed',bottom:'10px',right:'10px',zIndex:'10000',padding:'12px',background:'#20212c',color:'#fff',borderRadius:'10px',font:'11px/1.6 monospace',whiteSpace:'pre-wrap',maxWidth:'95vw'});
 out.textContent='Measuring first file row…';document.body.append(out);
 function check() {
  const row=Array.from(document.querySelectorAll('.files-list__row')).find(n=>!n.className.includes('skeleton')&&(!expected||n.textContent.includes(expected))&&n.getBoundingClientRect().height>0);
  if(!row)return;
  const ms=Number(performance.now().toFixed(1));out.dataset.readyMs=String(ms);
  const resources=performance.getEntriesByType('resource').filter(r=>/\.(js|css)(\?|$)/.test(r.name));
  out.dataset.assetBytes=String(resources.reduce((n,r)=>n+r.encodedBodySize,0));
  out.textContent='Full workspace first file row: '+ms+' ms\nScript/style network bytes so far: '+out.dataset.assetBytes;
  observer.disconnect();
 }
 const observer=new MutationObserver(check);observer.observe(document.body,{childList:true,subtree:true});check();
})();
