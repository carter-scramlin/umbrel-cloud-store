/* SPDX-License-Identifier: AGPL-3.0-or-later */
'use strict';
(() => {
 // Keep chunks small enough for mobile connections. Only chunk PUTs are retried:
 // a final MOVE may have succeeded even if its response was lost.
 async function sendFile(file, destination, signal, client) {
  const mtime=String(Math.floor(file.lastModified/1000));
  const common={'Content-Type':'application/octet-stream','X-OC-Mtime':mtime};
  if(file.size<=8*1024*1024) {
   await client.request(destination,{method:'PUT',headers:{...common,'If-None-Match':'*'},body:file,signal});
   return;
  }
  if(file.size>16*1024*1024*1024)throw Error('This browser supports files up to 16 GiB. Use the native client for larger files.');
  const session=new URL(client.uploadRoot+encodeURIComponent(client.uid)+'/umbrel-drive-'+client.uuid()).href;
  const headers={Destination:destination,'OC-Total-Length':String(file.size)};
  let assembled=false;
  await client.request(session,{method:'MKCOL',headers,signal});
  try {
   const chunkSize=Math.max(8*1024*1024,Math.ceil(file.size/9999));
   for(let offset=0,index=1;offset<file.size;offset+=chunkSize,index++) {
    const chunk=file.slice(offset,Math.min(offset+chunkSize,file.size));
    for(let attempt=0;;attempt++) {
     if(signal.aborted)throw new DOMException('Upload canceled','AbortError');
     try {await client.request(session+'/'+String(index).padStart(5,'0'),{method:'PUT',headers:{...headers,'Content-Type':'application/octet-stream'},body:chunk,signal});break;}
     catch(e) {
      if(signal.aborted||attempt>=2||!e.message.startsWith('Connection interrupted.'))throw e;
      client.progress(null,'Connection interrupted. Retrying this chunk…');
      await new Promise(resolve=>setTimeout(resolve,1000*(attempt+1)));
     }
    }
    client.progress(Math.floor(Math.min(offset+chunkSize,file.size)/file.size*100),'Uploading chunk '+index+'…');
   }
   client.progress(100,'Saving the completed file…');
   await client.request(session+'/.file',{method:'MOVE',headers:{...headers,'X-OC-Mtime':mtime,Overwrite:'F'},signal});
   assembled=true;
  } finally {
   if(!assembled)try{await client.request(session,{method:'DELETE',timeoutMs:15000});}catch{/* Server expires abandoned sessions after 24 hours. */}
  }
 }
 if(typeof module!=='undefined'&&module.exports){module.exports={sendFile};return;}
 const $ = id => document.getElementById(id);
 const config = document.body.dataset;
 const csrf = document.head.dataset.requesttoken;
 const root = new URL(config.davRoot + encodeURIComponent(config.uid) + '/');
 const collator = new Intl.Collator(undefined, {numeric:true, sensitivity:'base'});
 const state = {dir:'/', entries:[], limit:200, request:0, controller:null, first:null};
 let transfer = null;
 const metrics = {fresh:[], initial:0};
 const xmlProps = '<d:getlastmodified/><d:getcontentlength/><d:getcontenttype/><d:resourcetype/><d:getetag/><oc:fileid/><oc:favorite/><oc:permissions/>';
 const xml = '<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop>'+xmlProps+'</d:prop></d:propfind>';
 function el(tag, text, className) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(className)n.className=className; return n; }
 function normal(path) {
  const parts=path.split('/').filter(Boolean);
  if(parts.some(p=>p==='.'||p==='..'||p.includes('\u0000')))throw Error('Choose a valid folder path.');
  return '/'+parts.join('/');
 }
 function child(dir, name) {
  if(!name.trim()||name==='.'||name==='..'||/[\/\u0000]/.test(name))throw Error('Enter a name without slashes.');
  return normal(dir+'/'+name);
 }
 function dav(path, folder=false) { return root.href + normal(path).split('/').filter(Boolean).map(encodeURIComponent).join('/') + (folder&&path!=='/'?'/':''); }
 function workspace(entry, details=false) {
  if(entry?.id)return config.fileLink+encodeURIComponent(entry.id)+(details?'?opendetails=true&openfile=false':'');
  return config.full+'?dir='+encodeURIComponent(state.dir);
 }
 function error(message) { $('error').textContent=message; $('error').hidden=!message; }
 function status(message) { $('status').textContent=message; }
 async function request(url, options={}) {
  const target=new URL(url,location.href);
  if(target.origin!==location.origin)throw Error('This request must stay on your Drive.');
  const timeout=new AbortController();
  const canceled=()=>timeout.abort();
  if(options.signal?.aborted)canceled();
  options.signal?.addEventListener('abort',canceled,{once:true});
  const deadline=setTimeout(()=>timeout.abort(),options.timeoutMs||120000);
  let response;
  try {response=await fetch(target,{credentials:'same-origin',...options,signal:timeout.signal,headers:{requesttoken:csrf,'X-Requested-With':'XMLHttpRequest',...options.headers}});}
  catch(e) {
   if(options.signal?.aborted)throw new DOMException('Upload canceled','AbortError');
   throw Error(timeout.signal.aborted?'Connection interrupted. The request timed out. Try again.':'Connection interrupted. Check your network and try again.');
  } finally {clearTimeout(deadline);options.signal?.removeEventListener('abort',canceled);}
  if(!response.ok) {
   if(response.status===401)throw Error('Your session ended. Reload this page to sign in.');
   if(response.status===403)throw Error('You do not have permission for this action.');
   if([409,412].includes(response.status))throw Error('That name already exists or the file changed. Refresh and try again.');
   if(response.status===423)throw Error('This file is locked. Try again after editing has finished.');
   if(response.status===413)throw Error('The server rejected this file size. Try a smaller file or use the native client.');
   if(response.status===507)throw Error('There is not enough storage for this upload.');
   if(response.status===404)throw Error('This folder or file is no longer available. Refresh or choose My files.');
   throw Error('Drive could not complete this action (HTTP '+response.status+').');
  }
  return response;
 }
 function prop(node,ns,name) { return node.getElementsByTagNameNS(ns,name)[0]?.textContent||''; }
 function parseListing(text) {
  const doc=new DOMParser().parseFromString(text,'application/xml');
  if(doc.querySelector('parsererror'))throw Error('Drive returned an unexpected response. Reload to sign in again.');
  const entries=[];
  for(const item of doc.getElementsByTagNameNS('DAV:','response')) {
   const href=prop(item,'DAV:','href');
   const url=new URL(href,location.href);
   if(url.origin!==root.origin||!url.pathname.startsWith(root.pathname))continue;
   const path=normal(decodeURIComponent(url.pathname.slice(root.pathname.length)));
   if(path===state.dir){const permissions=prop(item,'http://owncloud.org/ns','permissions');state.canCreate=permissions.includes('C');continue;}
   const p=Array.from(item.getElementsByTagNameNS('DAV:','propstat')).find(n=>/\s200\s/.test(prop(n,'DAV:','status')));
   if(!p)continue;
   entries.push({path,name:path.split('/').at(-1),folder:p.getElementsByTagNameNS('DAV:','collection').length>0,
    size:Number(prop(p,'DAV:','getcontentlength'))||0,modified:prop(p,'DAV:','getlastmodified'),
    type:prop(p,'DAV:','getcontenttype'),etag:prop(p,'DAV:','getetag'),id:prop(p,'http://owncloud.org/ns','fileid'),permissions:prop(p,'http://owncloud.org/ns','permissions'),favorite:prop(p,'http://owncloud.org/ns','favorite')==='1'});
  }
  return entries;
 }
 function size(bytes) {if(bytes<1024)return bytes+' B';const units=['KB','MB','GB','TB'];let n=bytes/1024,i=0;while(n>=1024&&i<3){n/=1024;i++;}return n.toLocaleString(undefined,{maximumFractionDigits:1})+' '+units[i];}
 function updateMetrics(ms) {
  metrics.fresh.push(Number(ms.toFixed(1)));if(metrics.fresh.length>30)metrics.fresh.shift();
  if(state.first===null){state.first=performance.now();metrics.initial=Number(state.first.toFixed(1));}
  const node=$('drive-metrics');
  node.dataset.readyMs=String(metrics.initial);node.dataset.listingMs=String(metrics.fresh.at(-1));node.dataset.samples=JSON.stringify(metrics.fresh);node.dataset.entryCount=String(state.entries.length);
  node.textContent='First folder rows ready: '+metrics.initial+' ms\nLatest folder request + layout: '+metrics.fresh.at(-1)+' ms\nEntries: '+state.entries.length+' · visible rows: '+Math.min(state.limit,state.entries.length)+'\nRecent fresh loads (ms): '+metrics.fresh.join(', ');
 }
 function breadcrumbs() {
  const node=$('breadcrumbs');node.replaceChildren();let path='';
  const parts=[['My files','/'],...state.dir.split('/').filter(Boolean).map(name=>{path+='/'+name;return[name,path];})];
  for(const [i,[name,dir]] of parts.entries()) {
   if(i)node.append(el('span','/'));
   const a=el('a',name);a.href='?dir='+encodeURIComponent(dir);a.addEventListener('click',e=>{e.preventDefault();load(dir);});node.append(a);
  }
  $('full-workspace').href=workspace();
  document.querySelectorAll('.nav-item[data-dir]').forEach(n=>n.classList.toggle('active',n.dataset.dir==='/'?state.dir==='/':state.dir===n.dataset.dir||state.dir.startsWith(n.dataset.dir+'/')));
 }
 function render() {
  const filter=$('search').value.trim().toLocaleLowerCase();
  const mode=$('sort').value;
  const items=state.entries.filter(e=>e.name.toLocaleLowerCase().includes(filter)).sort((a,b)=>Number(b.folder)-Number(a.folder)||(mode==='modified'?Date.parse(b.modified)-Date.parse(a.modified):mode==='size'?b.size-a.size:0)||collator.compare(a.name,b.name));
  const fragment=document.createDocumentFragment();
  for(const entry of items.slice(0,state.limit)) {
   const row=el('tr');row.dataset.fileName=entry.name;
   const td=el('td');const a=el('a',undefined,'file-name');a.href=entry.folder?'?dir='+encodeURIComponent(entry.path):workspace(entry);
   const icon=el('span',entry.folder?'▰':(entry.name.split('.').at(-1)||'FILE').slice(0,4).toUpperCase(),'file-icon'+(entry.folder?'':' document'));icon.setAttribute('aria-hidden','true');
   a.append(icon,el('span',entry.name+(entry.favorite?' ☆':''),'name'));a.addEventListener('click',e=>{if(entry.folder){e.preventDefault();load(entry.path);}else if(/^image\/(png|jpeg|gif|webp|avif|bmp)$/.test(entry.type)){e.preventDefault();preview(entry);}});td.append(a);
   const date=el('td',entry.modified?new Date(entry.modified).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'}):'—','date-column');
   const bytes=el('td',entry.folder?'—':size(entry.size),'size-column');const actions=el('td',undefined,'row-actions');const menu=el('button','⋯');menu.type='button';menu.setAttribute('aria-label','Actions for '+entry.name);menu.addEventListener('click',()=>showActions(entry));actions.append(menu);row.append(td,date,bytes,actions);fragment.append(row);
  }
  $('new-folder').disabled=!state.canCreate;$('upload').disabled=Boolean(transfer)||!state.canCreate;
  $('new-folder').title=$('upload').title=state.canCreate?'':'This folder is read-only.';
  $('rows').replaceChildren(fragment);$('empty').hidden=items.length!==0;$('empty').querySelector('h2').textContent=filter?'No matching files.':'Room for something new.';
  $('empty').querySelector('p').textContent=filter?'Try another name in this folder.':'Drop files here, upload, or create a folder.';
  $('count').textContent=items.length+(items.length===1?' item':' items')+(items.length>state.limit?' · showing '+state.limit:'')+(filter?' in this folder':'');
  $('more').hidden=items.length<=state.limit;
 }
 async function load(dir, push=true, quiet=false) {
  const start=performance.now();const id=++state.request;
  state.controller?.abort();state.controller=new AbortController();
  try {
   dir=normal(dir);if(push||dir!==state.dir){state.limit=200;$('search').value='';}state.dir=dir;error('');state.loading=true;
   $('folder-title').textContent=dir==='/'?'My files':dir.split('/').at(-1);document.title=$('folder-title').textContent+' · Umbrel Drive';breadcrumbs();
   if(push){const u=new URL(location.href);u.searchParams.set('dir',dir);history.pushState({},'',u);}
   if(!quiet){$('rows').replaceChildren();$('empty').hidden=true;$('loading').hidden=false;}$('file-list').setAttribute('aria-busy','true');
   const response=await request(dav(dir,true),{method:'PROPFIND',headers:{Depth:'1','Content-Type':'application/xml; charset=utf-8'},body:xml,signal:state.controller.signal});
   const text=await response.text();if(id!==state.request)return;
   state.entries=parseListing(text);render();
   // Complete layout before timing it. Background tabs throttle animation frames;
   // waiting for one here would add up to a second to otherwise finished loads.
   $('file-list').getBoundingClientRect();if(id!==state.request)return;
   updateMetrics(performance.now()-start);status('Up to date');
  } catch(e) {if(e.name!=='AbortError'&&id===state.request){state.entries=[];$('rows').replaceChildren();error(e.message);status('Could not open this folder.');}}
  finally {if(id===state.request){state.loading=false;$('loading').hidden=true;$('file-list').setAttribute('aria-busy','false');}}
 }
 function closeDialog() {$('action-dialog').close();}
 function dialog(title, message='') {
  state.dialog=(state.dialog||0)+1;
  const d=$('action-dialog');if(d.open)d.close();d.replaceChildren();const heading=el('h2',title);heading.id='dialog-title';d.append(heading);if(message)d.append(el('p',message));d.showModal();return d;
 }
 function ask(title, fields, action, label='Save', message='') {
  const d=dialog(title,message);const generation=state.dialog;const form=el('form');const inputs={};
  for(const field of fields) {const l=el('label',field.label);const input=el('input');input.name=field.name;input.type=field.type||'text';input.value=field.value||'';input.required=Boolean(field.required);input.autocomplete='off';if(field.readOnly)input.readOnly=true;l.append(input);form.append(l);inputs[field.name]=input;}
  const problem=el('p',undefined,'dialog-error');problem.setAttribute('role','alert');form.append(problem);const buttons=el('div',undefined,'buttons');const cancel=el('button','Cancel','secondary');cancel.type='button';cancel.onclick=closeDialog;
  const submit=el('button',label,label==='Delete'?'danger':'primary');submit.type='submit';buttons.append(cancel,submit);form.append(buttons);d.append(form);
  form.onsubmit=async e=>{e.preventDefault();submit.disabled=true;cancel.disabled=true;problem.textContent='';try{await action(Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value])));if(d.open&&state.dialog===generation)d.close();}catch(err){problem.textContent=err.message;}finally{submit.disabled=false;cancel.disabled=false;}};
  Object.values(inputs)[0]?.focus();return d;
 }
 async function refreshAfter(action) {await action();await load(state.dir,false);}
 function showActions(entry) {
  const d=dialog(entry.name,entry.folder?'Folder':size(entry.size)+' · '+(entry.modified?new Date(entry.modified).toLocaleString():''));const list=el('div',undefined,'action-list');
  function button(name,handler) {const b=el('button',name);b.onclick=handler;list.append(b);}
  const open=el('a',entry.folder?'Open folder':'Open in full workspace');open.href=entry.folder?'?dir='+encodeURIComponent(entry.path):workspace(entry);if(entry.folder)open.onclick=e=>{e.preventDefault();closeDialog();load(entry.path);};list.append(open);
  if(!entry.folder){const download=el('a','Download');download.href=dav(entry.path);download.download=entry.name;list.append(download);}
  if(entry.permissions.includes('R'))button('Share link',()=>share(entry).catch(e=>error(e.message)));
  button(entry.favorite?'Remove favorite':'Add favorite',async()=>{try{const result=await request(dav(entry.path),{method:'PROPPATCH',headers:{'Content-Type':'application/xml'},body:'<d:propertyupdate xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:set><d:prop><oc:favorite>'+(entry.favorite?'0':'1')+'</oc:favorite></d:prop></d:set></d:propertyupdate>'});const resultXml=new DOMParser().parseFromString(await result.text(),'application/xml');if(resultXml.querySelector('parsererror')||!resultXml.getElementsByTagNameNS('DAV:','status').length||!Array.from(resultXml.getElementsByTagNameNS('DAV:','status')).every(n=>/\s200\s/.test(n.textContent)))throw Error('This storage could not update the favorite.');closeDialog();await load(state.dir,false);}catch(e){error(e.message);}});
  if(entry.permissions.includes('N'))button('Rename',()=>ask('Rename',[{name:'name',label:'Name',value:entry.name,required:true}],async v=>refreshAfter(async()=>{const parent=entry.path.slice(0,entry.path.lastIndexOf('/'))||'/';const target=child(parent,v.name);if(target===entry.path)return;await request(dav(entry.path),{method:'MOVE',headers:{Destination:dav(target),Overwrite:'F',...(entry.etag?{'If-Match':entry.etag}:{})}});}),'Rename'));
  for(const method of ['MOVE','COPY'].filter(method=>method==='COPY'||entry.permissions.includes('V')))button(method==='MOVE'?'Move to folder…':'Copy to folder…',()=>ask(method==='MOVE'?'Move to folder':'Copy to folder',[{name:'folder',label:'Destination folder',value:'/',required:true}],async v=>refreshAfter(async()=>{const target=child(normal(v.folder),entry.name);if(target===entry.path)throw Error('Choose a different folder.');await request(dav(entry.path),{method,headers:{Destination:dav(target),Overwrite:'F',...(entry.etag?{'If-Match':entry.etag}:{})}});}),method==='MOVE'?'Move':'Copy','Enter a folder path such as /Documents. Existing files are never replaced.'));
  const details=el('a',entry.folder?'Folder details & permissions':'Details, versions & activity');details.href=workspace(entry,true);list.append(details);
  if(entry.permissions.includes('D'))button('Delete',()=>ask('Delete “'+entry.name+'”?',[],async()=>refreshAfter(()=>request(dav(entry.path),{method:'DELETE',headers:entry.etag?{'If-Match':entry.etag}:{}})),'Delete','Check Trash in the full workspace to recover items supported by this storage.'));
  d.append(list);const done=el('button','Done','secondary');done.onclick=closeDialog;d.append(done);
 }
 async function ocs(path='',method='GET',data) {
  const response=await request(config.ocs+path+(path.includes('?')?'&':'?')+'format=json',{method,headers:{'OCS-APIRequest':'true',...(data?{'Content-Type':'application/x-www-form-urlencoded'}:{})},body:data?new URLSearchParams(data):undefined});
  const json=await response.json();if(json.ocs?.meta?.status==='failure')throw Error(json.ocs.meta.message||'Could not update sharing.');return json.ocs.data;
 }
 async function share(entry) {
  const d=dialog('Share “'+entry.name+'”','Link permissions and visibility follow your Drive settings.');const generation=state.dialog;const progress=el('p','Loading links…');d.append(progress);
  let links;try{links=await ocs('?path='+encodeURIComponent(entry.path)+'&reshares=true');}catch(e){progress.textContent=e.message;return;}
  if(!d.open||state.dialog!==generation)return;progress.remove();
  for(const link of links.filter(x=>Number(x.share_type)===3)) {
   const label=el('label','Share link');const input=el('input');input.value=String(link.url||'');input.readOnly=true;input.className='copy-link';label.append(input);d.append(label);
   const controls=el('div',undefined,'buttons');const copy=el('button','Copy link','secondary');copy.onclick=async()=>{try{await navigator.clipboard.writeText(input.value);copy.textContent='Copied';}catch{input.focus();input.select();copy.textContent='Select and copy';}};
   const revoke=el('button','Revoke link','secondary');revoke.onclick=()=>ask('Revoke this link?',[],async()=>{await ocs('/'+encodeURIComponent(link.id),'DELETE');status('Link revoked.');},'Revoke','Anyone using this link will lose access.');controls.append(copy,revoke);d.append(controls);
  }
  if(!links.some(x=>Number(x.share_type)===3))d.append(el('p','No public links for this item.'));
  const create=el('button','Create protected link','primary');create.onclick=()=>ask('Create share link',[{name:'password',label:'Link password (optional)',type:'password'},{name:'expiry',label:'Expiration date (optional)',type:'date'}],async v=>{await ocs('','POST',{path:entry.path,shareType:'3',permissions:'1',...(v.password?{password:v.password}:{}),...(v.expiry?{expireDate:v.expiry}:{})});status('Link created. Open Share link to copy it.');},'Create link','This creates a read-only link. Use the full workspace for users, groups and upload requests.');d.append(create);
  const done=el('button','Done','secondary');done.onclick=closeDialog;d.append(done);
 }
 function preview(entry) {const d=dialog(entry.name);const img=el('img',undefined,'preview');img.src=dav(entry.path);img.alt=entry.name;img.onerror=()=>{img.remove();d.prepend(el('p','This image could not be previewed. Open it in the full workspace to download or inspect it.'));};d.append(img);const done=el('button','Done','secondary');done.onclick=closeDialog;d.append(done);}
 async function upload(files) {
  if(!files.length||transfer)return;
  if(!state.canCreate){error('This folder is read-only. Choose a writable folder for uploads.');return;}
  const dir=state.dir;const button=$('upload');button.disabled=true;error('');let completed=0;
  transfer=new AbortController();$('transfer').hidden=false;
  try {
   for(const file of files) {
    if(transfer.signal.aborted)throw new DOMException('Upload canceled','AbortError');
    $('transfer-title').textContent=file.name+' · '+(completed+1)+' of '+files.length;
    $('transfer-progress').value=0;$('transfer-detail').textContent='Uploading '+size(file.size)+'…';
    status('Uploading '+file.name+'…');
    await sendFile(file,dav(child(dir,file.name)),transfer.signal,{request,uploadRoot:config.uploadRoot,uid:config.uid,uuid:()=>crypto.randomUUID(),progress:(value,message)=>{if(value!==null)$('transfer-progress').value=value;$('transfer-detail').textContent=message;}});completed++;
   }
   status('Uploaded '+completed+(completed===1?' file.':' files.'));
  } catch(e){error(e.name==='AbortError'?'Upload canceled. Completed files are kept.':e.message+' Completed files are kept. Check this folder before retrying.');status(completed+' uploads completed.');}
  finally {
   transfer=null;button.disabled=false;$('file-input').value='';$('transfer').hidden=true;
   const message=$('status').textContent;
   // Refresh without hiding an upload error or its completion summary.
   const problem=$('error').textContent;
   if(state.dir===dir)await load(dir,false);
   if(problem)error(problem);status(message);
  }
 }
 $('cancel-upload').onclick=()=>transfer?.abort();
 addEventListener('beforeunload',e=>{if(transfer){e.preventDefault();e.returnValue='';}});
 const navigation=$('navigation-toggle');
 navigation.onclick=()=>{const expanded=navigation.getAttribute('aria-expanded')!=='true';navigation.setAttribute('aria-expanded',String(expanded));$('drive-sidebar').classList.toggle('expanded',expanded);};
 $('drive-sidebar').addEventListener('click',e=>{if(e.target.closest('a')){navigation.setAttribute('aria-expanded','false');$('drive-sidebar').classList.remove('expanded');}});
 document.querySelectorAll('[data-dir]').forEach(n=>n.addEventListener('click',e=>{e.preventDefault();load(n.dataset.dir);}));
 $('new-folder').onclick=()=>{const dir=state.dir;ask('New folder',[{name:'name',label:'Folder name',required:true}],async v=>{await request(dav(child(dir,v.name),true),{method:'MKCOL'});if(state.dir===dir)await load(dir,false);},'Create folder');};
 $('upload').onclick=()=>$('file-input').click();$('file-input').onchange=()=>upload(Array.from($('file-input').files));
 $('refresh').onclick=()=>load(state.dir,false);$('search').oninput=()=>{state.limit=200;render();};$('sort').onchange=render;$('more').onclick=()=>{state.limit+=200;render();};
 addEventListener('popstate',()=>load(new URL(location.href).searchParams.get('dir')||'/',false));
 setInterval(()=>{if(document.visibilityState==='visible'&&!state.loading&&!$('action-dialog').open&&!transfer&&!$('file-list').contains(document.activeElement)&&document.activeElement!==$('search'))load(state.dir,false,true);},30000);
 let dragging=0;document.addEventListener('dragenter',e=>{if(Array.from(e.dataTransfer.types).includes('Files')){e.preventDefault();dragging++;document.body.classList.add('drop-active');}});document.addEventListener('dragleave',()=>{if(--dragging<=0){dragging=0;document.body.classList.remove('drop-active');}});document.addEventListener('dragover',e=>{if(Array.from(e.dataTransfer.types).includes('Files'))e.preventDefault();});document.addEventListener('drop',e=>{e.preventDefault();dragging=0;document.body.classList.remove('drop-active');if(Array.from(e.dataTransfer.items).some(item=>item.webkitGetAsEntry?.()?.isDirectory)){error('For folder uploads, use the full workspace or the Linux client.');return;}upload(Array.from(e.dataTransfer.files));});
 load(new URL(location.href).searchParams.get('dir')||'/',false);
})();
