var raw = String(variables.last_message||"").replace(/^```(?:json)?\s*\n?/,"").replace(/\n?```$/,"").trim();
var p = null;
try { p = JSON.parse(raw); } catch(e){ p = null; }
if (p === null){ var a = raw.indexOf("{"); var b = raw.lastIndexOf("}"); if (a>=0 && b>a){ try { p = JSON.parse(raw.slice(a,b+1)); } catch(e2){ p = null; } } }
if (p === null){ return JSON.stringify({gate:"QUARANTINE_ALL",reason:"unparseable_input",sa_verdict:"MISSING",perPost:[],promote:[],quarantine:[]}); }
function norm(s){ return String(s||"").toLowerCase().replace(/\s+/g," "); }
var tr = p.trend||{};
var title = String(tr.title||"");
var angle = String(p.angle||"");
var srcExcerpt = String(p.source_excerpt||"");
var sav = String(p.sa_verdict||"").toUpperCase();
var posts = Array.isArray(p.posts)? p.posts : [];

// ---------------------------------------------------------------------------
// FAIL-CLOSED PRECONDITIONS — must run BEFORE any per-post grading.
// Without these the grading loop iterates an empty array, flags nothing, and
// the aggregate falls through to PROMOTE_ALL, which is the gate's exact
// inverse: a consumer branching on `gate` would promote unvetted content.
// ---------------------------------------------------------------------------
function halt(reason, plats){
  return JSON.stringify({gate:"QUARANTINE_ALL",reason:reason,sa_verdict:sav||"MISSING",
                         perPost:[],promote:[],quarantine:plats||[]});
}
var plats = posts.map(function(x){ return x.platform||"?"; });
if (!Array.isArray(p.posts)) { return halt("missing_posts_array", []); }
if (posts.length === 0)      { return halt("empty_posts_array", []); }
if (sav !== "VERIFIED")      { return halt("score_unverified:"+(sav||"MISSING"), plats); }
if (!title)                  { return halt("no_source_title", plats); }

var BANNED = /\b(game[- ]?changer|game[- ]?changing|revolutioniz\w*|revolutionary|groundbreaking|paradigm shift|harness the power|unlock potential|changes everything)\b/i;
var FILLER = /\b(signals? a (new era|shift)|new era of|raises? the bar|witnessed? a leap|leap forward|leap in|redefin\w*|pushes? (the )?(limits|boundaries)|to new heights|next level|ushers? in|sets? a new standard|the future of|stay(?:ing)? ahead|unprecedented|significant progress|marks? a shift|smarter ai tools|more reliable than ever|best[- ]ever)\b/i;

// Widened: the original recognised only "% x times fold points hours tokens k",
// so "90 percent" and "$400 million" were never treated as stats at all.
var STAT = /(?:\$\s?\d[\d,]*(?:\.\d+)?\s*(?:k|m|bn|b|million|billion|trillion)?)|(?:\d[\d,]*(?:\.\d+)?\s*(?:%|percent|x\b|times|fold|points|hours|tokens|k\b|m\b|bn\b|million|billion|trillion))/gi;

// Whole-token grounding. The original test was ALLOWED.indexOf(stat) against a
// whitespace-stripped concatenation of all source fields, so "5x" matched
// inside "15x" and a fabricated figure passed as grounded. Tokenising both
// sides removes that, and stops a stat straddling two concatenated fields.
function statTokens(s){
  var out = {};
  var m = String(s||"").toLowerCase().match(STAT) || [];
  for (var i=0;i<m.length;i++){ out[m[i].replace(/[\s,]/g,"")] = true; }
  return out;
}
var SOURCE_STATS = statTokens(title+" "+(tr.source_url||"")+" "+angle+" "+srcExcerpt);

function titleTokens(t){ return (norm(t).match(/[a-z0-9][a-z0-9.\-]{2,}/g)||[]).filter(function(w){return ["the","and","for","with","that","this","next","model","new"].indexOf(w)===-1;}); }
var toks = titleTokens(title);

function gradePost(po){
  var text = String(po.text||"");
  var flags = [];
  var stats = String(text).toLowerCase().match(STAT)||[];
  for (var i=0;i<stats.length;i++){
    var nm = stats[i].replace(/[\s,]/g,"");
    if (SOURCE_STATS[nm] !== true) flags.push("UNGROUNDED_STAT:"+stats[i].trim());
  }
  if (BANNED.test(text)){ var b=text.match(BANNED); flags.push("BANNED_PHRASE:"+(b?b[0]:"?")); }
  if (FILLER.test(text)){ var f=text.match(FILLER); flags.push("LOW_SPECIFICITY:"+(f?f[0]:"?")); }
  var hasAnchor=false; var nt=norm(text);
  for (var t2=0;t2<toks.length;t2++){ if (nt.indexOf(toks[t2])!==-1){ hasAnchor=true; break; } }
  // toks is guaranteed non-empty: the no_source_title precondition returns
  // before this point, so NO_ANCHOR can no longer silently disable itself.
  if (!hasAnchor) flags.push("NO_ANCHOR");
  return { platform: po.platform||"?", decision: flags.length? "QUARANTINE":"PROMOTE", flags: flags };
}

var per = posts.map(gradePost);
var promote = per.filter(function(x){return x.decision==="PROMOTE";}).map(function(x){return x.platform;});
var quarantine = per.filter(function(x){return x.decision==="QUARANTINE";}).map(function(x){return x.platform;});
return JSON.stringify({ gate: quarantine.length? (promote.length? "QUARANTINE_SOME":"QUARANTINE_ALL"):"PROMOTE_ALL", sa_verdict: sav, perPost: per, promote: promote, quarantine: quarantine });
