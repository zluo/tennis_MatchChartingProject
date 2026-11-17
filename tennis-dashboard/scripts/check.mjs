import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summarize,select} from '../dist/analytics.mjs';
const data=JSON.parse(readFileSync(new URL('../dist/data.json',import.meta.url)));
assert(data.length>10000);
assert.equal(new Set(data.map(m=>m.id)).size,data.length);
for(const m of data){assert.equal(m.stats.length,2);for(const s of m.stats){assert(m.players.includes(s.player));assert(s.first_won+s.second_won<=s.serve_pts);assert(s.bp_saved<=s.bk_pts);}}
const sample=[{gender:'w',surface:'Hard',date:'20260101',players:['A','B'],stats:[{player:'A',serve_pts:10,first_won:6,second_won:2},{player:'B',serve_pts:90,first_won:40,second_won:10}]}];
assert(Math.abs(summarize(sample).serveWon-58)<1e-10);
assert.equal(summarize(sample,'a').serveWon,80);
assert.equal(summarize([]).serveWon,null);
assert.equal(select(sample,{player:'a',from:2026,to:2026}).length,1);
assert.equal(select(sample,{tour:'m'}).length,0);
assert.equal(select(sample,{from:2027,to:2026}).length,0);
console.log(`Validated ${data.length} matches and weighted-rate/filter behavior.`);
