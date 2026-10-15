/* Shared early-voting helpers: today's date in Central time, state status, and the rotating red banner. */
(function(){
  var MS=864e5;
  function todayCT(){
    var p=new Intl.DateTimeFormat("en-CA",{timeZone:"America/Chicago",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
    return Date.parse(p+"T00:00:00Z");
  }
  function day(s){return Date.parse(s+"T00:00:00Z")}
  function fmt(s,withDay){
    return new Date(s+"T12:00:00Z").toLocaleDateString("en-US",withDay?{weekday:"short",month:"short",day:"numeric",timeZone:"UTC"}:{month:"short",day:"numeric",timeZone:"UTC"});
  }
  function status(st,t){
    if(!st.start&&!st.end)return{k:"none",label:"No regular early voting"};
    if(!st.start)return{k:"varies",label:"In person at county office until "+fmt(st.end)};
    var a=day(st.start),b=day(st.end);
    if(t<a){var n=Math.round((a-t)/MS);return{k:"soon",days:n,label:n===1?"Opens tomorrow":"Opens in "+n+" days"};}
    if(t<=b){var left=Math.round((b-t)/MS);return{k:"open",days:left,label:left===0?"Last day today":"Open now, "+(left+1)+" days left"};}
    return{k:"closed",label:"Early voting has ended"};
  }
  window.CSGVote={todayCT:todayCT,day:day,fmt:fmt,status:status};

  function link(st,data){return st.link||data.sources.polling}

  function buildBanner(data){
    var el=document.getElementById("votebar"); if(!el)return;
    var t=todayCT(), eday=day(data.election);
    if(t>eday){el.remove();return;}
    var msgs=[], seen={};
    function add(st,text){ if(seen[st.ab+text])return; seen[st.ab+text]=1; msgs.push({st:st,text:text}); }
    var by={}; data.states.forEach(function(s){by[s.ab]=s});
    // featured states first (Texas)
    (data.featured||[]).forEach(function(ab){
      var s=by[ab], x=status(s,t);
      if(x.k==="soon")add(s,"<b>"+s.name+"</b> early in-person voting starts "+fmt(s.start,true));
      else if(x.k==="open")add(s,"<b>"+s.name+"</b> early voting is open through "+fmt(s.end,true));
    });
    var list=data.states.slice();
    // opening within the next 7 days, soonest first
    list.filter(function(s){var x=status(s,t);return x.k==="soon"&&x.days<=7}).sort(function(a,b){return day(a.start)-day(b.start)})
      .forEach(function(s){add(s,"<b>"+s.name+"</b> early voting starts "+fmt(s.start,true))});
    // opened in the last 3 days
    list.filter(function(s){var x=status(s,t);return x.k==="open"&&(t-day(s.start))/MS<=3}).forEach(function(s){add(s,"<b>"+s.name+"</b> early voting is open now through "+fmt(s.end))});
    // closing within 2 days
    list.filter(function(s){var x=status(s,t);return x.k==="open"&&x.days<=2}).forEach(function(s){add(s,"Last chance in <b>"+s.name+"</b>: early voting ends "+fmt(s.end,true))});
    var dleft=Math.round((eday-t)/MS);
    msgs.push({st:null,text:dleft===0?"<b>Election Day is today.</b> Polls are open":"<b>Election Day is Tuesday, Nov 3</b>, "+dleft+" day"+(dleft===1?"":"s")+" away"});

    var txt=el.querySelector(".vb-msg"), go=el.querySelector(".vb-go"), i=0, timer=null;
    function show(k){
      var m=msgs[k];
      txt.innerHTML=m.text;
      go.href=m.st?link(m.st,data):data.sources.polling;
      go.textContent=m.st&&m.st.link?"Find where to vote in "+m.st.name:"Find your polling place";
    }
    show(0); el.hidden=false;
    var reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
    if(msgs.length<2||reduce)return;
    function next(){ txt.classList.add("out"); setTimeout(function(){ i=(i+1)%msgs.length; show(i); txt.classList.remove("out"); },280); }
    function start(){ if(!timer)timer=setInterval(next,4500); }
    function stop(){ clearInterval(timer); timer=null; }
    el.addEventListener("mouseenter",stop); el.addEventListener("mouseleave",start);
    el.addEventListener("focusin",stop); el.addEventListener("focusout",start);
    start();
  }
  window.CSGVoteData=fetch("/data/early-voting.json",{cache:"no-cache"}).then(function(r){return r.json()});
  window.CSGVoteData.then(buildBanner).catch(function(){});
})();
