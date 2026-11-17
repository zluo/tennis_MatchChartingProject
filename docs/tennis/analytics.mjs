export const sum=(rows,key)=>rows.reduce((n,r)=>n+(Number(r[key])||0),0);
export const rate=(a,b)=>b ? a/b*100 : null;
export function summarize(matches,player=''){
 const stats=matches.flatMap(m=>m.stats.filter(s=>!player||s.player.toLowerCase()===player.toLowerCase()));
 const serve=sum(stats,'serve_pts'),returns=sum(stats,'return_pts');
 return {stats,serve,returns,serveWon:rate(sum(stats,'first_won')+sum(stats,'second_won'),serve),returnWon:rate(sum(stats,'return_pts_won'),returns),firstIn:rate(sum(stats,'first_in'),serve),aces:rate(sum(stats,'aces'),serve),breakSaved:rate(sum(stats,'bp_saved'),sum(stats,'bk_pts'))};
}
export function select(matches,{tour='',surface='',from=0,to=9999,player=''}){
 return matches.filter(m=>(!tour||m.gender===tour)&&(!surface||m.surface===surface)&&Number(m.date.slice(0,4))>=from&&Number(m.date.slice(0,4))<=to&&(!player||m.players.some(p=>p.toLowerCase()===player.toLowerCase())));
}

// A player's own statistics, ordered oldest to newest; no results inferred.
export function athleteHistory(matches, player) {
 if (!player) return [];
 return matches.flatMap(match => {
  const stats = match.stats.find(s => s.player.toLowerCase() === player.toLowerCase());
  if (!stats) return [];
  return [{id:match.id,date:match.date,tournament:match.tournament,surface:match.surface,
   opponent:match.players.find(p=>p.toLowerCase()!==player.toLowerCase()) || '',
   ...summarize([{stats:[stats]}],player)}];
 }).sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
}
