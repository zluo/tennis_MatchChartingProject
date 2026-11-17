import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as analytics from '../docs/tennis/analytics.mjs';
const data=JSON.parse(readFileSync(new URL('../docs/tennis/data.json',import.meta.url)));
const profiles=JSON.parse(readFileSync(new URL('../docs/tennis/profiles.json',import.meta.url)));
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
 await run(document,async url=>({ok:true,json:async()=>url==='profiles.json'?profiles:data}),analytics.sum,analytics.rate,analytics.summarize,analytics.select,analytics.athleteHistory,{search});
 assert(!nodes.get('status').textContent.startsWith('Could not load'));
 return nodes;
}
test('overview runs without athlete-page elements and links selected player',async()=>{
 const nodes=await load('index.html','app.js');assert(!nodes.has('athlete'));
 nodes.get('player').value='Roger Federer';nodes.get('player').listeners.change();
 assert.equal(nodes.get('athleteLink').href,'athlete.html?player=Roger%20Federer');
 assert(nodes.get('surfaceChart').innerHTML.includes('<svg'));
 assert(nodes.get('trendChart').innerHTML.includes('<rect'));
 assert(!nodes.get('trendChart').innerHTML.includes('<polyline'));
 assert(!nodes.get('trendChart').innerHTML.includes('<circle'));
});
test('separate athlete page supports direct links, filters, and full history',async()=>{
 const nodes=await load('athlete.html','athlete.js','?player=Roger%20Federer');
 assert(!nodes.has('surfaceChart'));assert.equal(nodes.get('tour').value,'m');
 assert(nodes.get('historyChart').innerHTML.includes('<rect'));
 assert(nodes.get('historyChart').innerHTML.includes('viewBox="0 0 540 240"'));
 assert(!nodes.get('historyChart').innerHTML.includes('min-width'));
 const athleteMatches=data.filter(m=>m.players.includes('Roger Federer'));
 const annualYears=new Set(athleteMatches.map(m=>m.date.slice(0,4)));
 assert((nodes.get('historyChart').innerHTML.match(/data-year=/g)||[]).length<=annualYears.size);
 const year=athleteMatches[0].date.slice(0,4);
 const annual=analytics.summarize(athleteMatches.filter(m=>m.date.startsWith(year)),'Roger Federer');
 assert(nodes.get('historyChart').innerHTML.includes(annual.serveWon.toFixed(1)+'%'));
 assert(!nodes.get('historyChart').innerHTML.includes('<polyline'));
 assert(!nodes.get('historyChart').innerHTML.includes('<circle'));
 assert(nodes.get('matchRows').innerHTML.includes('Roger Federer'));
 assert(nodes.get('activityChart').innerHTML.includes('data-result="win"'));
 assert(nodes.get('activityChart').innerHTML.includes('data-result="loss"'));
 assert(nodes.get('activityChart').innerHTML.includes('wins,'));
 nodes.get('surface').value='Unknown';nodes.get('surface').listeners.change();
 assert(nodes.get('athleteSummary').textContent.startsWith('No charted'));
 nodes.get('fullHistory').onclick();assert(nodes.get('historyChart').innerHTML.includes('<rect'));
 nodes.get('reset').onclick();assert.equal(nodes.get('athlete').value,'');
 assert.equal(nodes.get('status').textContent,'Choose an athlete to begin.');
});

test('tour lists are separate, rank-sorted, and show lifetime charted period',async()=>{
 const nodes=await load('athlete.html','athlete.js');
 let choices=nodes.get('athlete').innerHTML;
 assert(choices.includes('Serena Williams'));assert(!choices.includes('Roger Federer'));
 const rankedWomen=profiles.filter(p=>p.gender==='w'&&p.rank!==null).sort((a,b)=>a.rank-b.rank);
 assert(choices.indexOf(rankedWomen[0].name)<choices.indexOf('Rank unavailable'));
 const womenOptions=[...choices.matchAll(/<option value="([^"]+)">/g)].map(m=>m[1]);
 assert.deepEqual(womenOptions.slice(0,rankedWomen.length),rankedWomen.map(p=>p.name));
 nodes.get('tour').value='m';nodes.get('tour').listeners.change();
 choices=nodes.get('athlete').innerHTML;assert(choices.includes('Roger Federer'));assert(!choices.includes('Serena Williams'));
 const men=profiles.filter(p=>p.gender==='m'&&p.rank!==null).sort((a,b)=>a.rank-b.rank);
 const options=[...choices.matchAll(/<option value="([^"]+)">/g)].map(m=>m[1]);
 assert.equal(options[0],men[0].name);
 nodes.get('athlete').value='Roger Federer';nodes.get('athlete').onchange();
 const profile=profiles.find(p=>p.name==='Roger Federer');
 assert(nodes.get('athleteProfile').innerHTML.includes(profile.first.slice(0,4)+'–'+profile.last.slice(0,4)));
 nodes.get('tour').value='w';nodes.get('tour').listeners.change();
 assert.equal(nodes.get('player').value,'');assert.equal(nodes.get('athleteProfile').innerHTML,'');
});
