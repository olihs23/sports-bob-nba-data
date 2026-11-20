/* Sports Bob official NBA.com advanced-stat cards.
 * Explicit opt-in: does not replace any existing UI or touch the database.
 * Load official-advanced-adapter.js before this file. No prediction logic.
 */
(function (root) {
  "use strict";
  const STYLE_ID = "sportsbob-official-advanced-styles";
  const css = [
    ".sba-card{font:inherit;color:inherit;border:1px solid #34505a;background:#142632;border-radius:14px;padding:14px;margin:10px 0;min-width:0}",
    ".sba-head{display:flex;gap:10px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;margin-bottom:11px}",
    ".sba-title{font-weight:750;font-size:16px;line-height:1.35}",
    ".sba-tag{font-size:10px;color:#9ee6d7;background:#173c3b;border:1px solid #2b6965;padding:5px 8px;border-radius:999px}",
    ".sba-meta,.sba-foot{font-size:11px;line-height:1.55;color:#b3c4ca}",
    ".sba-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}",
    ".sba-stat{background:#1d3441;border:1px solid #2c4b57;border-radius:10px;padding:11px 8px;min-width:0}",
    ".sba-number{font-weight:800;font-variant-numeric:tabular-nums;font-size:clamp(17px,3.5vw,24px);letter-spacing:-.035em;overflow-wrap:anywhere}",
    ".sba-label{font-size:10px;color:#b0c6cb;margin-top:4px}",
    ".sba-secondary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-top:9px}",
    ".sba-secondary .sba-number{font-size:16px}",
    ".sba-foot{border-top:1px solid #2b4651;padding-top:9px;margin-top:11px}",
    ".sba-versus{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:10px}",
    ".sba-missing{border:1px dashed #5e7076;border-radius:11px;padding:12px;color:#c9d5da;font-size:12px}",
    "@media(max-width:600px){.sba-card{padding:11px}.sba-versus{grid-template-columns:1fr}.sba-secondary{grid-template-columns:repeat(2,minmax(0,1fr))}}"
  ].join("\n");
  let pending = null;
  const requestIds = new WeakMap();
  function nextRequest(el) { const id=(requestIds.get(el)||0)+1;requestIds.set(el,id);return id; }
  function isCurrent(el,id) { return requestIds.get(el)===id; }
  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, x =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[x]);
  }
  function fmt(value, digits=1, signed=false) {
    if(!Number.isFinite(value)) return "—";
    const s=value.toFixed(digits);
    return signed && value>0 ? "+"+s : s;
  }
  function pct(value) {return Number.isFinite(value) ? fmt(value*100)+"%" : "—";}
  function captured(status) {
    if (!status?.captureDate) return "Snapshot capture time unavailable";
    const t=new Date(status.captureDate);
    return Number.isNaN(t.getTime()) ? "Snapshot capture time unavailable" :
      "Frozen snapshot · "+t.toLocaleDateString("en-US",{timeZone:"America/New_York",year:"numeric",month:"short",day:"numeric"});
  }
  function tile(label,value) {
    return '<div class="sba-stat"><div class="sba-number">'+esc(value)+
      '</div><div class="sba-label">'+esc(label)+'</div></div>';
  }
  function renderCard(player,status,compact) {
    if(!player) return '<div class="sba-missing">NBA.com advanced ratings unavailable for this player.</div>';
    const m=player.metrics||{};
    const primary=tile("OFFRTG",fmt(m.OFF_RATING))+
      tile("DEFRTG",fmt(m.DEF_RATING))+
      tile("NETRTG",fmt(m.NET_RATING,1,true));
    const secondary=compact ? "" : '<div class="sba-secondary">'+
      tile("Usage",pct(m.USG_PCT))+tile("TS%",pct(m.TS_PCT))+
      tile("AST%",pct(m.AST_PCT))+tile("REB%",pct(m.REB_PCT))+'</div>';
    return '<section class="sba-card" aria-label="Official NBA advanced stats for '+esc(player.playerName)+'">'+
      '<div class="sba-head"><div><div class="sba-title">'+esc(player.playerName)+
      ' <span class="sba-meta">· '+esc(player.team)+'</span></div>'+
      '<div class="sba-meta">'+esc(player.gamesPlayed)+' GP · '+
      esc(fmt(player.minutesPerGame))+' MIN/game · 2026–27</div></div>'+
      '<span class="sba-tag">NBA.com published fields</span></div>'+
      '<div class="sba-grid">'+primary+'</div>'+secondary+
      '<div class="sba-foot">'+esc(captured(status))+
      ' · Ratings describe team performance while this player was on court, not isolated individual skill. '+
      'E_* estimates and third-party substitutes are never used.</div></section>';
  }
  function adapter() {
    const a=root.SportsBobOfficialAdvanced;
    if(!a||typeof a.load!=="function") throw new Error("Official NBA adapter has not loaded");
    return a;
  }
  async function ensureData() {
    const a=adapter();
    if(a.getStatus()) return a;
    if(!pending) pending=a.load().then(()=>a).catch(err=>{pending=null;throw err;});
    return pending;
  }
  function style() {
    if(typeof document==="undefined"||document.getElementById(STYLE_ID)) return;
    const el=document.createElement("style");
    el.id=STYLE_ID;el.textContent=css;document.head.appendChild(el);
  }
  function target(el) {
    if(!el||typeof el.innerHTML!=="string")throw new TypeError("Provide an existing DOM container");
    return el;
  }
  async function mountPlayer(element,playerId) {
    const el=target(element);style();
    const current=nextRequest(el);
    try{
      const a=await ensureData(),p=a.getPlayer(playerId);
      if(!isCurrent(el,current)) return {stale:true,found:!!p,frozen:true};
      el.innerHTML=renderCard(p,a.getStatus(),false);
      return {found:!!p,playerId:String(playerId),frozen:true};
    }catch(e){
      if(!isCurrent(el,current)) return {stale:true,found:false,frozen:true};
      el.innerHTML='<div class="sba-missing">Official NBA advanced stats unavailable: '+esc(e.message)+'</div>';
      return {found:false,error:String(e.message),frozen:true};
    }
  }
  async function mountMatchup(element,leftPlayerId,rightPlayerId) {
    const el=target(element);style();
    const current=nextRequest(el);
    try{
      const a=await ensureData();
      const l=a.getPlayer(leftPlayerId),r=a.getPlayer(rightPlayerId);
      if(!isCurrent(el,current)) return {stale:true,bothFound:!!(l&&r),frozen:true,advantage:null};
      el.innerHTML='<div class="sba-versus">'+renderCard(l,a.getStatus(),true)+
        renderCard(r,a.getStatus(),true)+'</div>'+
        '<p class="sba-meta">Descriptive ratings only. No matchup advantage or prop projection is inferred.</p>';
      return {bothFound:!!(l&&r),advantage:null,frozen:true};
    }catch(e){
      if(!isCurrent(el,current)) return {stale:true,bothFound:false,frozen:true,advantage:null};
      el.innerHTML='<div class="sba-missing">Official NBA matchup stats unavailable: '+esc(e.message)+'</div>';
      return {bothFound:false,advantage:null,frozen:true,error:String(e.message)};
    }
  }
  root.SportsBobOfficialAdvancedCards=Object.freeze({ensureData,mountPlayer,mountMatchup,
    renderPlayer:(p,s)=>renderCard(p,s,false),
    renderMatchup:(l,r,s)=>'<div class="sba-versus">'+renderCard(l,s,true)+renderCard(r,s,true)+'</div>'});
})(typeof window!=="undefined"?window:globalThis);
