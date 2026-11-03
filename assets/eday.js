/* Election Day call-out (Nov 3, 2026). Shows only on Election Day, Central time, and removes itself after. */
(function(){
  function ct(){var p={};new Intl.DateTimeFormat("en-US",{timeZone:"America/Chicago",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(new Date()).forEach(function(x){p[x.type]=x.value});return p;}
  var n=ct(); if(n.year+"-"+n.month+"-"+n.day!=="2026-11-03")return;
  var mins=19*60-(+n.hour*60+ +n.minute), open=mins>0;
  var left=open?(mins>=60?Math.floor(mins/60)+" hr "+(mins%60)+" min":mins+" min")+" until Texas polls close":"Texas polls are closed. Results start rolling in tonight.";
  var css=document.createElement("style");
  css.textContent='.eday{background:linear-gradient(90deg,#b8362e,#c8262a 55%,#a62a24);color:#fff6e3;border-bottom:6px solid #f5a21f;position:relative;overflow:hidden}'
  +'.eday::before{content:"\\2605  \\2605  \\2605  \\2605  \\2605  \\2605  \\2605  \\2605  \\2605  \\2605  \\2605  \\2605";position:absolute;top:6px;left:0;right:0;text-align:center;letter-spacing:.9em;font-size:12px;color:rgba(255,246,227,.25);white-space:nowrap;overflow:hidden}'
  +'.eday .in{max-width:1180px;margin:0 auto;padding:30px 24px 28px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:20px 32px}'
  +'.eday .k{font-family:"Archivo Narrow","Arial Narrow",sans-serif;font-weight:700;letter-spacing:.18em;text-transform:uppercase;font-size:15px;color:#ffd27a;margin:0 0 4px}'
  +'.eday h2{font-family:"Anton",Impact,"Arial Narrow",sans-serif;font-weight:400;text-transform:uppercase;font-size:clamp(40px,6.4vw,78px);line-height:.95;margin:0;color:#fff6e3;letter-spacing:.01em;text-shadow:0 3px 0 rgba(0,0,0,.25)}'
  +'.eday p.s{margin:8px 0 0;font-size:18px;max-width:52ch;color:#ffe9d2}.eday p.s b{color:#fff}'
  +'.eday .t{display:inline-block;margin-top:12px;font-family:"Archivo Narrow","Arial Narrow",sans-serif;font-weight:700;font-size:17px;background:rgba(0,0,0,.22);padding:6px 14px;border-radius:999px}'
  +'.eday .ctas{display:flex;flex-direction:column;gap:12px;min-width:260px}'
  +'.eday a.b{display:block;text-align:center;font-family:"Archivo Narrow","Arial Narrow",sans-serif;font-weight:700;font-size:19px;text-decoration:none;padding:15px 22px;border-radius:4px}'
  +'.eday a.b1{background:#f5a21f;color:#0c1e38}.eday a.b1:hover{background:#ffb646}'
  +'.eday a.b2{border:2px solid #fff6e3;color:#fff6e3}.eday a.b2:hover{background:rgba(255,246,227,.12)}'
  +'@media (max-width:700px){.eday .in{padding:24px 16px}.eday .ctas{width:100%}}';
  document.head.appendChild(css);
  var el=document.createElement("section"); el.className="eday"; el.id="election-day"; el.setAttribute("aria-label","Election Day");
  el.innerHTML='<div class="in"><div><p class="k">★ Election Day is today ★</p><h2>Let\'s swamp the vote!</h2>'
   +(open?'<p class="s"><b>If you haven\'t voted, go now.</b> Texas polls close at 7 p.m. Central. In line by 7? Stay in line, you still get to vote. Already voted? Grab five people who haven\'t.</p>'
         :'<p class="s"><b>Thank you to everyone who showed up.</b> Stay tuned, the numbers start tonight.</p>')
   +'<span class="t">'+left+'</span></div>'
   +'<div class="ctas"><a class="b b1" href="/vote/" data-eday="polling">Find your polling place</a><a class="b b2" href="/abbott-impact/" data-eday="abbott">Nudge your friends with Abbott Impact</a></div></div>';
  function place(){
    var anchor=document.querySelector("header.bar")||document.querySelector(".csg-top")||document.body.firstElementChild;
    if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(el,anchor.nextSibling); else document.body.insertBefore(el,document.body.firstChild);
    el.addEventListener("click",function(e){var a=e.target.closest("a[data-eday]");if(a&&typeof gtag==="function")gtag("event","election_day_click",{destination:a.getAttribute("data-eday"),page_path:location.pathname});});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",place); else place();
})();
