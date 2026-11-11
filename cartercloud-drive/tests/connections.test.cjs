// SPDX-FileCopyrightText: 2026 Carter Cloud
// SPDX-License-Identifier: AGPL-3.0-or-later
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {libraryContext,umbrelCopyTarget,quotaSummary,uploadId}=require('../server/umbreldrive/js/fast.js');
const connected={owner:true,libraries:{files:'connected',photos:'read-only'}};
test('connected library context respects mount boundaries and owner isolation',()=>{
 assert.equal(libraryContext('/Umbrel Files/subfolder',connected).name,'Umbrel Files');
 assert.match(libraryContext('/Umbrel Photos',connected).description,/manage photo backup and deletion/);
 assert.equal(libraryContext('/Umbrel Files copy',connected),null);
 assert.equal(libraryContext('/Umbrel Files',{owner:true,libraries:{files:'name-conflict'}}),null);
 assert.equal(libraryContext('/Umbrel Files',{owner:false,libraries:{}}),null);
});
test('copy shortcut is limited to writable owner connection and preserves existing paths',()=>{
 assert.equal(umbrelCopyTarget({path:'/Documents/café.txt',name:'café.txt'},connected),'/Umbrel Files/café.txt');
 for(const path of ['/Umbrel Files','/Umbrel Files/test.txt','/Umbrel Photos'])assert.equal(umbrelCopyTarget({path,name:'file'},connected),null);
 for(const connections of [{owner:false,libraries:{}},{owner:true,libraries:{files:'read-only'}},{owner:true,libraries:{files:'disconnected'}}])assert.equal(umbrelCopyTarget({path:'/file',name:'file'},connections),null);
 assert.equal(umbrelCopyTarget({path:'/Umbrel Files copy',name:'Umbrel Files copy'},connected),'/Umbrel Files/Umbrel Files copy');
});
test('quota does not present unknown unlimited or malformed values as free space',()=>{
 assert.deepEqual(quotaSummary('1024','0'),{used:1024,available:0});
 for(const value of ['','-1','-2','unknown','Infinity','1e9','9007199254740992'])assert.deepEqual(quotaSummary(value,value),{used:null,available:null});
});

test('HTTP upload IDs retain secure random bytes when randomUUID is unavailable',()=>{
 assert.equal(uploadId({getRandomValues:bytes=>{bytes.fill(255);return bytes;}}),'ffffffff-ffff-4fff-bfff-ffffffffffff');
 assert.equal(uploadId({randomUUID:()=> 'native-id'}),'native-id');
});
