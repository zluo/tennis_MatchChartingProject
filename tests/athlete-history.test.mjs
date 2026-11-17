import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {athleteHistory,select} from '../docs/tennis/analytics.mjs';
const match=(id,date,player,other,serve,first,second)=>({id,date,gender:'m',surface:'Hard',tournament:'Example',players:[player,other],stats:[{player,serve_pts:serve,first_won:first,second_won:second,return_pts:0},{player:other,serve_pts:100,first_won:90,second_won:0}]});
test('history sorts by date and uses the athlete’s statistics, including player two',()=>{
 const matches=[match('later','20250102','Other','Athlete',100,90,0),match('early','20240102','Athlete','Other',10,5,2)];
 const history=athleteHistory(matches,'athlete');
 assert.deepEqual(history.map(h=>h.id),['early','later']);
 assert.equal(history[0].serveWon,70);
 assert.equal(history[1].serveWon,90);
 assert.equal(history[0].returnWon,null);
 assert.equal(history[0].opponent,'Other');
 assert.equal(matches[0].id,'later');
});
test('empty selections and unmatched athletes are safe',()=>{
 assert.deepEqual(athleteHistory([], 'Athlete'),[]);
 assert.deepEqual(athleteHistory([match('a','20240101','A','B',0,0,0)],'C'),[]);
 assert.deepEqual(athleteHistory([],''),[]);
});
test('zero denominators stay missing and filters constrain history',()=>{
 const matches=[match('a','20240101','A','B',0,0,0),match('b','20250101','A','B',10,5,0)];
 assert.equal(athleteHistory(matches,'A')[0].serveWon,null);
 assert.deepEqual(athleteHistory(select(matches,{from:2025,to:2025}), 'A').map(h=>h.id),['b']);
});
test('real athlete history matches source overview rows',()=>{
 const data=JSON.parse(readFileSync(new URL('../docs/tennis/data.json',import.meta.url)));
 for(const athlete of ['Roger Federer','Serena Williams']){
  const history=athleteHistory(data,athlete);assert(history.length>10);
  for(let i=0;i<history.length;i++){
   const h=history[i];if(i)assert(history[i-1].date<=h.date);
   const source=data.find(m=>m.id===h.id).stats.find(s=>s.player===athlete);
   const expected=source.serve_pts?(source.first_won+source.second_won)/source.serve_pts*100:null;
   assert.equal(h.serveWon,expected);
   assert.notEqual(h.opponent,athlete);
  }
 }
});
test('dropdown contains every athlete before JavaScript loads',()=>{
 const html=readFileSync(new URL('../docs/tennis/athlete.html',import.meta.url),'utf8');
 const data=JSON.parse(readFileSync(new URL('../docs/tennis/data.json',import.meta.url)));
 const select=html.match(/<select id="athlete">([\s\S]*?)<\/select>/)[1];
 const names=new Set(data.flatMap(m=>m.players));
 assert.equal((select.match(/<option /g)||[]).length,names.size+1);
 assert(select.includes('Roger Federer'));assert(select.includes('Serena Williams'));
 assert(html.includes('src="athlete.js?v=yearly-results-1"'));
 const app=readFileSync(new URL('../docs/tennis/app.js',import.meta.url),'utf8');
 assert(app.includes("analytics.mjs?v=yearly-results-1"));
});

test('athlete outcomes are relative to the selected player and preserve unknowns',()=>{
 const a=match('a','20250101','A','B',10,8,0);a.winner='A';
 const b=match('b','20250102','A','B',10,9,0);b.winner='B';
 const c=match('c','20250103','A','B',10,10,0);c.winner=null;
 assert.deepEqual(athleteHistory([a,b,c],'A').map(h=>h.result),['win','loss','unknown']);
 assert.deepEqual(athleteHistory([a,b,c],'B').map(h=>h.result),['loss','win','unknown']);
});
