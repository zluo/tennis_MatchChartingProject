import {sum,rate,summarize,select,athleteHistory} from './analytics.mjs';
const $=id=>document.getElementById(id),fmt=n=>Number(n).toLocaleString(),pct=n=>n===null?'—':n.toFixed(1)+'%',esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data=[],filtered=[],page=0;
const svg=(body,height=230)=>`<svg viewBox="0 0 540 ${height}" role="img">${body}</svg>`;
const text=(x,y,t,extra='')=>`<text x="${x}" y="${y}" ${extra}>${esc(t)}</text>`;
function bars(groups,series,colors){
 if(!groups.length)return '<p>No data for this selection.</p>';
 const h=Math.max(230,groups.length*53+40),max=100,left=72,width=400;
 let out=[0,25,50,75,100].map(v=>`<path d="M${left+v/100*width} 10V${h-25}" stroke="#e7ebe1"/>`+text(left+v/100*width,h-7,v+'%','text-anchor="middle"')).join('');
 groups.forEach((g,i)=>{const y=22+i*(h-45)/groups.length;out+=text(left-10,y+14,g.label,'text-anchor="end"');series.forEach((s,j)=>{let v=g[s];if(v!==null)out+=`<rect x="${left}" y="${y+j*14}" width="${Math.max(0,v)/max*width}" height="10" rx="3" fill="${colors[j]}"><title>${esc(g.label)}: ${pct(v)}</title></rect>`;});});return svg(out,h);
}
function trends(matches,player){
 const years=[...new Set(matches.map(m=>m.date.slice(0,4)))].sort();
 if(!years.length)return '<p>No data for this selection.</p>';
 const groups=years.map(y=>({y,...summarize(matches.filter(m=>m.date.startsWith(y)),player)}));
 let out=[0,20,40,60,80,100].map(v=>`<path d="M40 ${205-v*1.8}H520" stroke="#e7ebe1"/>`+text(32,209-v*1.8,v+'%','text-anchor="end"')).join('');
 const x=i=>years.length===1?280:45+i*465/(years.length-1),y=v=>205-v*1.8;
 ['firstIn','aces'].forEach((k,j)=>{const points=groups.map((g,i)=>g[k]===null?null:[x(i),y(g[k])]).filter(Boolean);out+=`<polyline points="${points.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${j?'#83b6ab':'#266449'}" stroke-width="3"/>`;groups.forEach((g,i)=>{if(g[k]!==null)out+=`<circle cx="${x(i)}" cy="${y(g[k])}" r="3" fill="${j?'#83b6ab':'#266449'}"><title>${g.y}: ${pct(g[k])} (${g.serve} serve points)</title></circle>`;});});
 years.forEach((v,i)=>{if(i===0||i===years.length-1||i%Math.ceil(years.length/6)===0)out+=text(x(i),228,v,'text-anchor="middle"');});return svg(out,240);
}
function renderAthlete(player){
 const history=athleteHistory(filtered,player);
 $('athlete').value=history.length?history[0].stats[0].player:player;
 $('athleteTitle').textContent=player?player+' · athlete history':'Choose an athlete to explore their history';
 $('fullHistory').disabled=!player;
 if(!history.length){
  const message=player?'No charted matches for this athlete under the current filters. Use “Show full history” to widen the selection.':'Choose an athlete to see their history.';
  $('athleteSummary').textContent=message;
  $('historyChart').innerHTML='<p>'+esc(message)+'</p>';$('activityChart').innerHTML='<p>'+esc(message)+'</p>';return;
 }
 const date=d=>d.replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3');
 $('athleteSummary').textContent=`${fmt(history.length)} charted matches · ${date(history[0].date)} to ${date(history.at(-1).date)} · ${new Set(history.map(h=>h.opponent)).size} opponents · current filters`;
 const metric=$('historyMetric').value,label=$('historyMetric').selectedOptions[0].textContent;
 const time=d=>Date.UTC(+d.slice(0,4),+d.slice(4,6)-1,+d.slice(6,8));
 const start=time(history[0].date),end=time(history.at(-1).date),x=d=>start===end?280:50+(time(d)-start)/(end-start)*455,y=v=>200-v*1.7;
 let plot='<title>'+esc(player+' — '+label+' by match')+'</title>';
 for(const v of [0,25,50,75,100])plot+=`<path d="M50 ${y(v)}H510" stroke="#e7ebe1"/>`+text(42,y(v)+4,v+'%','text-anchor="end"');
 // Null rates leave gaps instead of implying a value or connecting across missing data.
 let segment=[];const segments=[];
 history.forEach(h=>{if(h[metric]===null){if(segment.length)segments.push(segment);segment=[];}else segment.push(`${x(h.date)},${y(h[metric])}`);});if(segment.length)segments.push(segment);
 segments.forEach(points=>plot+=`<polyline points="${points.join(' ')}" fill="none" stroke="#266449" stroke-width="1.6" opacity=".65"/>`);
 history.forEach(h=>{if(h[metric]!==null)plot+=`<circle cx="${x(h.date)}" cy="${y(h[metric])}" r="3.5" fill="#266449"><title>${esc(date(h.date)+' · vs '+h.opponent+' · '+h.tournament+' · '+h.surface+' · '+label+': '+pct(h[metric]))}</title></circle>`;});
 if(start===end)plot+=text(280,225,date(history[0].date),'text-anchor="middle"');
 else for(let i=0;i<3;i++){const stamp=new Date(start+(end-start)*i/2).toISOString().slice(0,10);plot+=text(50+i*227.5,225,stamp,'text-anchor="middle"');}
 $('historyChart').innerHTML=svg(plot,240);
 const counts=new Map();history.forEach(h=>{const year=h.date.slice(0,4);counts.set(year,(counts.get(year)||0)+1);});
 const first=+history[0].date.slice(0,4),last=+history.at(-1).date.slice(0,4),years=Array.from({length:last-first+1},(_,i)=>String(first+i));
 const max=Math.max(...counts.values()),barWidth=460/years.length;
 let activity='<title>'+esc(player+' — charted matches per year')+'</title>';
 for(const v of [...new Set([0,Math.ceil(max/2),max])]){const yy=200-v/max*170;activity+=`<path d="M40 ${yy}H510" stroke="#e7ebe1"/>`+text(32,yy+4,v,'text-anchor="end"');}
 years.forEach((year,i)=>{const n=counts.get(year)||0;activity+=`<rect x="${45+i*barWidth}" y="${200-n/max*170}" width="${Math.max(1,barWidth-3)}" height="${n/max*170}" rx="2" fill="#83b6ab"><title>${year}: ${n} charted matches</title></rect>`;if(i===0||i===years.length-1||i%Math.ceil(years.length/5)===0)activity+=text(45+(i+.5)*barWidth,225,year,'text-anchor="middle"');});
 $('activityChart').innerHTML=svg(activity,240);
}
function render(){
 const player=$('player').value.trim();const from=+$('from').value,to=+$('to').value;
 filtered=select(data,{tour:$('tour').value,surface:$('surface').value,from,to,player}).sort((a,b)=>b.date.localeCompare(a.date));page=0;
 const s=summarize(filtered,player),points=filtered.reduce((n,m)=>n+sum(m.stats,'serve_pts'),0);
 $('status').textContent=from>to?'Choose a start year before the end year.':`${fmt(filtered.length)} charted matches · ${player||'All players'} · ${from}–${to} · hover over charts for exact values`;
 const metric=(title,value,desc)=>`<article class="metric"><div class="eyebrow">${title}</div><div class="value">${value}</div><small>${desc}</small></article>`;
 $('metrics').innerHTML=metric('CHARTED MATCHES',fmt(filtered.length),'In your current selection')+metric('RECORDED POINTS',fmt(points),'Across selected matches')+metric('SERVE POINTS WON',pct(s.serveWon),'First + second serve points')+metric('BREAK POINTS SAVED',pct(s.breakSaved),'Saved / break points faced');
 const surfaces=[...new Set(filtered.map(m=>m.surface))].sort().map(surface=>({label:surface||'Unknown',...summarize(filtered.filter(m=>m.surface===surface),player)}));
 $('surfaceChart').innerHTML=bars(surfaces,['serveWon','returnWon'],['#266449','#83b6ab']);
 const rally=['1-3','4-6','7-9','10'].map(label=>({label:label==='10'?'10+ shots':label+' shots',pts:filtered.reduce((n,m)=>n+m.rally.filter(r=>r[0]===label).reduce((a,r)=>a+r[1],0),0)}));
 const total=sum(rally,'pts');$('rallyChart').innerHTML=total?bars(rally.map(r=>({...r,share:rate(r.pts,total)})),['share'],['#266449']):'<p>No rally data for this selection.</p>';
 $('trendChart').innerHTML=trends(filtered,player);
 const best=surfaces.filter(s=>s.serveWon!==null).sort((a,b)=>b.serveWon-a.serveWon)[0];
 $('insights').innerHTML=filtered.length?`<ul><li>${best?`<strong>${esc(best.label)}</strong> has the highest serve point win rate in this selection: <strong>${pct(best.serveWon)}</strong> across ${fmt(best.serve)} serve points.`:'No serve statistics available.'}</li><li>${total?`Short rallies (1–3 shots) account for <strong>${pct(rate(rally[0].pts,total))}</strong> of ${fmt(total)} points with rally classifications.`:'No rally classifications available.'}</li><li><strong>${pct(s.aces)}</strong> of serve points end in an ace; <strong>${pct(s.firstIn)}</strong> begin with a successful first serve.</li></ul>`:'<p>No matches found. Try another player or widen the filters.</p>';
 $('export').disabled=!filtered.length;renderAthlete(player);renderTable();
}
function renderTable(){
 const pages=Math.max(1,Math.ceil(filtered.length/12));$('page').textContent=`${page+1} / ${pages}`;$('prev').disabled=page===0;$('next').disabled=page>=pages-1;$('matchCount').textContent=fmt(filtered.length)+' matches';
 $('matchRows').innerHTML=filtered.slice(page*12,page*12+12).map((m,i)=>`<tr><td>${esc(m.date.replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3'))}</td><td><strong>${esc(m.players.join(' vs '))}</strong></td><td>${esc(m.tournament)}</td><td><span class="pill">${esc(m.surface)}</span></td><td>${esc(m.round)}</td><td><button data-index="${page*12+i}">Analyze ↗</button></td></tr>`).join('')||'<tr><td colspan="6">No matching records.</td></tr>';
}
$('matchRows').addEventListener('click',e=>{const button=e.target.closest('button');if(!button)return;const m=filtered[+button.dataset.index];const fields=[['Serve points','serve_pts'],['Aces','aces'],['Double faults','dfs'],['Winners','winners'],['Unforced errors','unforced']];$('detailContent').innerHTML=`<span class="eyebrow">MATCH ANALYSIS</span><h2>${esc(m.players.join(' vs '))}</h2><p>${esc(m.tournament)} · ${esc(m.surface)} · ${esc(m.date)}</p><div class="tablewrap"><table><thead><tr><th>Metric</th>${m.stats.map(s=>`<th>${esc(s.player)}</th>`).join('')}</tr></thead><tbody>${fields.map(([label,key])=>`<tr><td>${label}</td>${m.stats.map(s=>`<td>${fmt(s[key])}</td>`).join('')}</tr>`).join('')}<tr><td>Serve points won</td>${m.stats.map(s=>`<td>${pct(summarize([{stats:[s]}]).serveWon)}</td>`).join('')}</tr></tbody></table></div><p>Winners and unforced errors follow the source overview definitions.</p>`;$('detail').showModal();});
$('close').onclick=()=>$('detail').close();$('prev').onclick=()=>{page--;renderTable();};$('next').onclick=()=>{page++;renderTable();};
$('export').onclick=()=>{const fields=['id','date','gender','tournament','surface','round'];const cell=v=>'"'+String(v).replaceAll('"','""')+'"';const csv=[fields.join(','),...filtered.map(m=>fields.map(f=>cell(m[f])).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='baseline-matches.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
try{const response=await fetch('data.json');if(!response.ok)throw Error('Dataset request failed');data=await response.json();
 const years=[...new Set(data.map(m=>m.date.slice(0,4)))].filter(y=>/^\d{4}$/.test(y)).sort();
 for(const id of ['from','to'])$(id).innerHTML=years.map(y=>`<option>${y}</option>`).join('');$('to').value=years.at(-1);
 $('surface').innerHTML+=[...new Set(data.map(m=>m.surface))].filter(Boolean).sort().map(s=>`<option>${esc(s)}</option>`).join('');
 const athletes=[...new Set(data.flatMap(m=>m.players))].sort();
 $('players').innerHTML=athletes.map(p=>`<option value="${esc(p)}">`).join('');
 $('athlete').innerHTML+=athletes.map(p=>`<option value="${esc(p)}">${esc(p)}</option>`).join('');
 $('athlete').onchange=()=>{$('player').value=$('athlete').value;syncTourToAthlete();render();};
 $('historyMetric').onchange=()=>renderAthlete($('player').value.trim());
 $('fullHistory').onclick=()=>{$('surface').value='';$('from').value=years[0];$('to').value=years.at(-1);syncTourToAthlete();render();};
 function syncTourToAthlete(){const player=$('player').value.trim().toLowerCase();if(!player)return;const tours=[...new Set(data.filter(m=>m.players.some(p=>p.toLowerCase()===player)).map(m=>m.gender))];if(tours.length)$('tour').value=tours.length===1?tours[0]:'';}

 for(const id of ['tour','surface','from','to','player'])$(id).addEventListener('change',()=>{if(id==='player')syncTourToAthlete();render();});
 $('reset').onclick=()=>{$('tour').value='w';$('surface').value='';$('from').value=years[0];$('to').value=years.at(-1);$('player').value='';render();};render();
}catch(error){$('status').textContent='Could not load match data. Serve this folder over HTTP and reload. '+error.message;}
