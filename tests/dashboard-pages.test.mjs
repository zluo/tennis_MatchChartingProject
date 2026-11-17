import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as analytics from '../docs/tennis/analytics.mjs';
const data=JSON.parse(readFileSync(new URL('../docs/tennis/data.json',import.meta.url)));
class Element {
 constructor(){this.value='';this.html='';this.listeners={};}
 set innerHTML(html){this.html=html;if(!this.value){const first=html.match(/<option(?: value="([^"]*)")?>([^<]*)<\/option>/);if(first)this.value=first[1]??first[2];}}
 get innerHTML(){return this.html;}
 get selectedOptions(){return [{textContent:'Serve points won'}];}
 addEventListener(name,handler){this.listeners[name]=handler;}
}
async function load(page,script,search=''){
 const html=readFileSync(new URL('../docs/tennis/'+page,import.meta.url),'utf8');
 const nodes=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new Element()]));
 for(const match of html.matchAll(/<select id="([^"]+)">([\s\S]*?)<\/select>/g))nodes.get(match[1]).innerHTML=match[2];
 const document={getElementById:id=>nodes.get(id)||null};
 const source=readFileSync(new URL('../docs/tennis/'+script,import.meta.url),'utf8').replace(/^import .*\n/,'');
 const run=new (Object.getPrototypeOf(async function(){}).constructor)('document','fetch','sum','rate','summarize','select','athleteHistory','location',source);
 await run(document,async()=>({ok:true,json:async()=>data}),analytics.sum,analytics.rate,analytics.summarize,analytics.select,analytics.athleteHistory,{search});
 assert(!nodes.get('status').textContent.startsWith('Could not load'));
 return nodes;
}
test('overview runs without athlete-page elements and links selected player',async()=>{
 const nodes=await load('index.html','app.js');assert(!nodes.has('athlete'));
 nodes.get('player').value='Roger Federer';nodes.get('player').listeners.change();
 assert.equal(nodes.get('athleteLink').href,'athlete.html?player=Roger%20Federer');
 assert(nodes.get('surfaceChart').innerHTML.includes('<svg'));
});
test('separate athlete page supports direct links, filters, and full history',async()=>{
 const nodes=await load('athlete.html','athlete.js','?player=Roger%20Federer');
 assert(!nodes.has('surfaceChart'));assert.equal(nodes.get('tour').value,'m');
 assert(nodes.get('historyChart').innerHTML.includes('<circle'));
 assert(nodes.get('matchRows').innerHTML.includes('Roger Federer'));
 nodes.get('surface').value='Unknown';nodes.get('surface').listeners.change();
 assert(nodes.get('athleteSummary').textContent.startsWith('No charted'));
 nodes.get('fullHistory').onclick();assert(nodes.get('historyChart').innerHTML.includes('<circle'));
 nodes.get('reset').onclick();assert.equal(nodes.get('athlete').value,'');
 assert.equal(nodes.get('status').textContent,'Choose an athlete to begin.');
});
