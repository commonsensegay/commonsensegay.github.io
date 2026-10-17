/* Google Analytics events for the clicks that matter: follows, volunteering, voting lookups, Log Cabin, shares. */
(function(){
  var PLAT=[["facebook.com","facebook"],["tiktok.com","tiktok"],["instagram.com","instagram"],["youtube.com","youtube"],["x.com","x"],["twitter.com","x"]];
  var VOL=[["abbottimpact.org","abbott_impact"],["earlyvoteaction.com","early_vote_action"],["protectthevote.com","protect_the_vote"]];
  var VOTE=["nass.org","votetexas.gov","vote.org","sos.","elections."];
  function where(a){
    var s=a.closest("[id],section,header,footer,nav,.dock,.votebar");
    if(!s)return "page";
    if(s.classList.contains("dock"))return "sticky_bar";
    if(s.classList.contains("votebar"))return "vote_banner";
    return s.id||s.className.split(" ")[0]||s.tagName.toLowerCase();
  }
  function send(name,params){ if(typeof gtag==="function")gtag("event",name,params); }
  // Abbott Impact: every click toward the app, and each time the section is actually seen
  function aiDest(a,href){
    var d=a.getAttribute("data-ai"); if(d)return d;
    if(href.indexOf("abbottimpact.org/register")>-1)return "register";
    if(href.indexOf("users.abbottimpact.org")>-1)return "login";
    if(href.indexOf("abbottimpact.org/app")>-1)return "download_page";
    if(href.indexOf("abbottimpact.org")>-1)return "website";
    if(href.indexOf("id6749019654")>-1)return "app_store";
    if(href.indexOf("com.rightimpact")>-1)return "google_play";
    if(/^\/abbott-impact\/?(#|$)|^#abbott-impact$/.test(href))return "learn_more";
    return null;
  }
  function aiSeen(){
    var els=document.querySelectorAll("[data-ai-view]"); if(!els.length||!("IntersectionObserver" in window))return;
    var io=new IntersectionObserver(function(es){es.forEach(function(en){
      if(en.isIntersecting){ send("abbott_impact_view",{section:en.target.getAttribute("data-ai-view"),page_path:location.pathname}); io.unobserve(en.target); }
    })},{threshold:0,rootMargin:"0px 0px -35% 0px"});
    els.forEach(function(el){io.observe(el)});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",aiSeen); else aiSeen();
  document.addEventListener("click",function(e){
    var a=e.target.closest&&e.target.closest("a,button"); if(!a)return;
    var href=(a.getAttribute("href")||"").toLowerCase(), loc=where(a), i;
    var ai=a.tagName==="A"?aiDest(a,href):null;
    if(ai)send("abbott_impact_click",{destination:ai,link_location:loc,page_path:location.pathname,outbound:/^https?:/.test(href)});
    if(a.tagName==="A"&&/^https?:/.test(href)){
      if(href.indexOf("facebook.com/sharer")>-1||href.indexOf("x.com/intent")>-1){
        send("share",{method:href.indexOf("facebook")>-1?"facebook":"x",content_type:"blog_post",item_id:location.pathname});return;
      }
      for(i=0;i<PLAT.length;i++)if(href.indexOf(PLAT[i][0])>-1){send("follow_click",{platform:PLAT[i][1],link_location:loc,page_path:location.pathname});return;}
      for(i=0;i<VOL.length;i++)if(href.indexOf(VOL[i][0])>-1){send("volunteer_click",{program:VOL[i][1],link_location:loc});return;}
      if(href.indexOf("logcabin")>-1){send("join_log_cabin_click",{link_location:loc});return;}
      for(i=0;i<VOTE.length;i++)if(href.indexOf(VOTE[i])>-1){send("polling_place_click",{link_url:href,link_location:loc});return;}
    }
    if(a.tagName==="BUTTON"&&/copy link/i.test(a.textContent)){send("share",{method:"copy_link",content_type:"blog_post",item_id:location.pathname});}
  },true);
})();
