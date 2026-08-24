"""LPRW v4 UI — dashboard + user portal."""

DASHBOARD = r'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#06080f">
<title>LPRW Panel</title>
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#06080f;--bg2:#0b0e18;--card:rgba(18,22,36,.92);--card2:#141825;
  --bd:rgba(255,255,255,.07);--bd2:rgba(255,255,255,.12);
  --tx:#eef1f8;--mu:#8b93a8;--mu2:#5c657a;
  --pr:#6366f1;--pr2:#818cf8;--ok:#34d399;--er:#f87171;--wn:#fbbf24;--cy:#22d3ee;
  --g:linear-gradient(135deg,#6366f1,#8b5cf6 50%,#d946ef);--r:16px;--side:260px;
  --shadow:0 20px 50px rgba(0,0,0,.45);
}
[data-theme="light"]{
  --bg:#f0f3fa;--bg2:#e6eaf5;--card:#fff;--card2:#f8fafc;
  --bd:rgba(15,23,42,.08);--bd2:rgba(15,23,42,.12);
  --tx:#0f172a;--mu:#64748b;--mu2:#94a3b8;--shadow:0 12px 36px rgba(15,23,42,.1);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Vazirmatn,system-ui,sans-serif;background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}
body::before{content:"";position:fixed;width:500px;height:500px;top:-100px;right:-80px;background:radial-gradient(circle,rgba(99,102,241,.25),transparent 70%);filter:blur(80px);pointer-events:none;z-index:0}
button,input,select,textarea{font-family:inherit;font-size:.9rem;color:var(--tx)}
.hidden{display:none!important}
::-webkit-scrollbar{width:7px}::-webkit-scrollbar-thumb{background:rgba(129,140,248,.3);border-radius:99px}

#login{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;position:relative;z-index:2}
.login-card{width:100%;max-width:420px;background:var(--card);border:1px solid var(--bd2);border-radius:24px;padding:40px 32px;box-shadow:var(--shadow)}.login-logo-img{display:block;width:92px;height:92px;object-fit:cover;border-radius:22px;margin:0 auto 18px;box-shadow:0 18px 45px rgba(99,102,241,.25);border:1px solid var(--bd2)}
.login-logo-wrap{display:flex;flex-direction:column;align-items:center;margin-bottom:18px}.login-logo-wrap img{width:96px;height:96px;object-fit:cover;border-radius:24px;border:1px solid var(--bd2);box-shadow:0 18px 50px rgba(99,102,241,.28)}.login-version{margin-top:9px;color:var(--mu);font-size:.72rem;font-weight:700;letter-spacing:.02em}.github-login{position:absolute;top:20px;right:20px;width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:rgba(255,255,255,.06);border:1px solid var(--bd2);color:var(--tx);transition:.18s;box-shadow:0 10px 30px rgba(0,0,0,.18)}.github-login:hover{transform:translateY(-2px);background:rgba(99,102,241,.12);border-color:rgba(129,140,248,.35)}.github-login svg{width:24px;height:24px;fill:currentColor}.login-card h1{font-size:1.7rem;font-weight:800;margin-bottom:6px}
.login-card .sub{color:var(--mu);margin-bottom:24px;font-size:.9rem}
.field{margin-bottom:14px}
.field label{display:block;font-size:.78rem;color:var(--mu);margin-bottom:6px;font-weight:600}
.field input,.field select,.field textarea{width:100%;padding:12px 14px;border-radius:12px;border:1px solid var(--bd2);background:rgba(0,0,0,.22);outline:none}
[data-theme="light"] .field input,[data-theme="light"] .field select{background:#f8fafc}
.field input:focus,.field select:focus{border-color:var(--pr);box-shadow:0 0 0 3px rgba(99,102,241,.18)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:10px 16px;border-radius:12px;border:1px solid var(--bd2);cursor:pointer;font-weight:700;background:var(--card2);color:var(--tx);transition:.15s}
.btn:hover{filter:brightness(1.08)}
.btn-p{background:var(--g);color:#fff;border:none;box-shadow:0 8px 24px rgba(99,102,241,.3)}
.btn-block{width:100%;padding:13px}
.btn-sm{padding:7px 11px;font-size:.8rem;border-radius:10px}
.btn-d{background:rgba(248,113,113,.12);color:var(--er);border-color:rgba(248,113,113,.25)}
.err{display:none;margin-top:10px;padding:10px;border-radius:10px;background:rgba(248,113,113,.12);color:var(--er);font-size:.85rem}

#app{display:none;min-height:100vh;position:relative;z-index:1}
.shell{display:grid;grid-template-columns:var(--side) 1fr;min-height:100vh}
.side{background:linear-gradient(180deg,var(--card),var(--bg2));border-left:1px solid var(--bd);padding:18px 12px;display:flex;flex-direction:column;gap:4px}
.side .logo{display:flex;align-items:center;gap:10px;padding:8px 10px 16px;border-bottom:1px solid var(--bd);margin-bottom:10px}
.side .logo .mk{width:38px;height:38px;border-radius:11px;background:var(--g);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:.9rem;color:#fff}
.side .logo h2{font-size:1rem;font-weight:800}
.side .logo small{color:var(--mu);font-size:.7rem}
.nav-item{display:flex;align-items:center;gap:10px;padding:11px 12px;border-radius:11px;color:var(--mu);cursor:pointer;font-weight:600;font-size:.88rem;border:1px solid transparent}
.nav-item:hover{background:rgba(99,102,241,.08);color:var(--tx)}
.nav-item.active{background:rgba(99,102,241,.14);color:var(--pr2);border-color:rgba(99,102,241,.22)}
.nav-item .nav-ico{width:20px;height:20px;display:grid;place-items:center;flex:0 0 20px;color:currentColor;opacity:.9}.nav-item .nav-ico svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.xray-status{display:inline-flex;align-items:center;gap:8px;font-weight:800}.xray-dot{width:8px;height:8px;border-radius:50%;display:inline-block;background:#22c77a!important;color:#22c77a;box-shadow:0 0 10px #22c77a!important}.xray-ok{color:#22c77a}.xray-mid{color:#fbbf24}.xray-bad{color:#ff4d62}.hero-metric.status-metric{border-color:rgba(255,255,255,.1)}.dashboard-stat .icon svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}

.brand-mark{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;position:relative;background:linear-gradient(135deg,#6366f1,#8b5cf6);box-shadow:0 10px 28px rgba(99,102,241,.28);overflow:hidden;color:#fff;font-weight:900;font-size:1.15rem}
.brand-mark:before{content:"";position:absolute;inset:7px;border:1px solid rgba(255,255,255,.42);border-radius:9px;transform:rotate(45deg)}
.brand-mark span{position:relative;z-index:2;font-family:ui-sans-serif,system-ui}
.brand-mark i{position:absolute;width:18px;height:3px;background:rgba(255,255,255,.85);border-radius:99px;bottom:9px;right:7px;transform:rotate(-45deg)}
.switch-row{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:15px 0;border-bottom:1px solid var(--bd);cursor:pointer}
.switch-row:last-child{border-bottom:0}
.switch-row span{display:flex;flex-direction:column;gap:3px}.switch-row small{color:var(--mu);font-size:.76rem;font-weight:400}
.switch-row input{appearance:none;width:48px;height:26px;border-radius:99px;background:var(--mu2);position:relative;cursor:pointer;transition:.2s;flex:0 0 auto}
.switch-row input:before{content:"";position:absolute;width:20px;height:20px;border-radius:50%;background:#fff;top:3px;right:25px;transition:.2s;box-shadow:0 2px 6px rgba(0,0,0,.25)}
.switch-row input:checked{background:var(--pr)}.switch-row input:checked:before{right:3px}
.actions-row{display:flex;gap:8px;flex-wrap:wrap}.outbound-preview{display:grid;gap:8px}.preview-row{display:flex;justify-content:space-between;gap:12px;padding:12px 14px;background:rgba(99,102,241,.06);border:1px solid var(--bd);border-radius:12px}.preview-row span{color:var(--mu)}
.chip-ok{color:var(--ok);border-color:rgba(52,211,153,.25);background:rgba(52,211,153,.08)}

.side-bottom{margin-top:auto;padding-top:14px;border-top:1px solid var(--bd);display:flex;flex-direction:column;gap:6px}
.main{padding:20px 24px 40px;max-width:1280px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:18px;flex-wrap:wrap}.top-brand{display:flex;align-items:center;gap:10px;margin-right:auto;margin-left:18px}.top-brand img{width:42px;height:42px;border-radius:12px;object-fit:cover;border:1px solid var(--bd2);box-shadow:0 8px 25px rgba(99,102,241,.18)}.top-brand div{display:flex;flex-direction:column;line-height:1.2}.top-brand b{font-size:.86rem}.top-brand small{color:var(--mu);font-size:.68rem;margin-top:3px}
.topbar h1{font-size:1.35rem;font-weight:800}
.kpis{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:16px;max-width:760px}
@media(max-width:560px){.kpis{grid-template-columns:1fr}}
@media(max-width:560px){.kpis{grid-template-columns:1fr}}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:12px 14px}
.kpi .t{font-size:.75rem;color:var(--mu);font-weight:600;margin-bottom:6px}
.kpi .v{font-size:1.2rem;font-weight:800}
.panel{background:var(--card);border:1px solid var(--bd);border-radius:var(--r);padding:18px;margin-bottom:14px}
.panel-h{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.panel-h h3{font-size:1rem;font-weight:800}
table{width:100%;border-collapse:collapse}
th,td{padding:11px 8px;text-align:right;border-bottom:1px solid var(--bd);font-size:.84rem}
th{color:var(--mu);font-weight:700;font-size:.73rem}
.badge{display:inline-block;padding:3px 9px;border-radius:99px;font-size:.72rem;font-weight:700}
.badge.on{background:rgba(52,211,153,.15);color:var(--ok)}
.badge.off{background:rgba(248,113,113,.15);color:var(--er)}
.chip{display:inline-flex;padding:4px 9px;border-radius:99px;font-size:.72rem;font-weight:700;background:rgba(99,102,241,.12);color:var(--pr2);border:1px solid rgba(99,102,241,.2);cursor:pointer}
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(5px);z-index:80;display:none;align-items:center;justify-content:center;padding:16px}
.modal-bg.show{display:flex}
.modal{background:var(--card);border:1px solid var(--bd2);border-radius:18px;padding:22px;width:100%;max-width:500px;box-shadow:var(--shadow);max-height:90vh;overflow:auto}
.modal h3{font-size:1.1rem;font-weight:800;margin-bottom:14px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:560px){.form-row{grid-template-columns:1fr}}
.toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%) translateY(16px);background:var(--card2);border:1px solid var(--bd2);padding:11px 16px;border-radius:12px;z-index:99;opacity:0;transition:.25s;font-weight:600}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.empty{text-align:center;padding:32px 14px;color:var(--mu)}
.chart-box{position:relative;height:240px}
.bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;z-index:60;background:var(--card);border-top:1px solid var(--bd);padding:6px 6px calc(7px + env(safe-area-inset-bottom));justify-content:space-around;gap:4px;box-shadow:0 -8px 28px rgba(0,0,0,.35)}.bottom-nav button{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px}.bn-ico{width:20px;height:20px;display:grid;place-items:center}.bn-ico svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.bottom-nav button{flex:1;border:none;background:transparent;color:var(--mu);font-family:inherit;font-size:.72rem;font-weight:700;padding:3px 4px;border-radius:10px;cursor:pointer;min-height:36px;line-height:1.2}
.bottom-nav button span{display:block;font-size:1.2rem;margin-bottom:1px}
.bottom-nav button.active{color:var(--pr2);background:rgba(99,102,241,.16)}
@media(max-width:900px){
  .shell{grid-template-columns:1fr}
  .side{display:none!important}
  .main{padding:14px 12px 110px}
  .bottom-nav{display:flex}
}
code{font-family:ui-monospace,monospace;font-size:.76rem;color:var(--pr2);word-break:break-all}

/* LPRW Modern UI v4.11 — premium dashboard */
:root{
  --bg:#070a10;--panel:#0f141d;--panel2:#151c27;--line:rgba(255,255,255,.075);
  --text:#f4f7fb;--muted:#8995a8;--accent:#7c5cff;--orange:#ff8a1f;
  --green:#22c77a;--purple:#a06cff;--gray:#87909d;--red:#ff4d62;
  --cyan:#2dd4bf;--shadow:0 22px 70px rgba(0,0,0,.38);
}
body{background:radial-gradient(circle at 12% -8%,rgba(124,92,255,.18),transparent 30%),radial-gradient(circle at 90% 10%,rgba(45,212,191,.07),transparent 26%),var(--bg)!important;color:var(--text)}
body:after{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;background-image:linear-gradient(rgba(255,255,255,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.018) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,black,transparent 72%)}
.side{background:linear-gradient(180deg,rgba(15,20,29,.98),rgba(8,11,17,.98))!important;border-left:1px solid var(--line)!important;box-shadow:18px 0 55px rgba(0,0,0,.18)}
.side .logo{padding-bottom:20px}.side .logo .mk{box-shadow:0 0 30px rgba(124,92,255,.28)}
.nav-item{position:relative;padding:13px 14px!important;margin:3px 0;border:1px solid transparent!important;border-radius:14px!important;transition:.2s ease!important;overflow:hidden}
.nav-item:before{content:"";width:4px;height:0;position:absolute;right:0;top:50%;transform:translateY(-50%);border-radius:8px;background:var(--accent);transition:.2s}
.nav-item:hover{background:linear-gradient(90deg,rgba(124,92,255,.05),rgba(124,92,255,.13))!important;color:#fff!important;transform:translateX(-2px)}
.nav-item.active{background:linear-gradient(90deg,rgba(124,92,255,.08),rgba(124,92,255,.20))!important;color:#a995ff!important;border-color:rgba(124,92,255,.22)!important;box-shadow:inset 0 0 25px rgba(124,92,255,.05),0 8px 25px rgba(0,0,0,.15)}
.nav-item.active:before{height:28px}
.main{padding:24px 28px 48px!important}.topbar{margin-bottom:22px!important}.topbar h1{font-size:1.55rem!important;letter-spacing:-.5px}
button,.btn{border:1px solid #303a49!important;border-radius:13px!important;background:linear-gradient(145deg,#1c2533,#10161f)!important;color:#f1f5f9!important;box-shadow:0 8px 22px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.035);transition:.2s ease!important;min-height:38px}
button:hover,.btn:hover{transform:translateY(-2px);border-color:#65738a!important;box-shadow:0 14px 32px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.05)}
button:active,.btn:active{transform:translateY(0) scale(.98)}
.btn-p,.primary{background:linear-gradient(135deg,#896fff,#5e43e9)!important;border-color:#9c8aff!important;box-shadow:0 10px 30px rgba(124,92,255,.28)!important}
.btn-p:hover{box-shadow:0 16px 38px rgba(124,92,255,.38)!important}
.btn-d{background:linear-gradient(145deg,rgba(255,77,98,.15),rgba(30,15,20,.8))!important;color:#ff7180!important;border-color:rgba(255,77,98,.3)!important}
.kpis{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:14px!important;max-width:none!important;margin-bottom:18px!important}
.kpi{position:relative;overflow:hidden;background:linear-gradient(145deg,rgba(18,24,34,.98),rgba(12,16,23,.98))!important;border:1px solid var(--line)!important;border-radius:18px!important;padding:16px 17px!important;min-height:112px;box-shadow:var(--shadow)!important}
.kpi:before{content:"";position:absolute;width:90px;height:90px;left:-28px;bottom:-38px;border-radius:50%;background:var(--accent);opacity:.10;filter:blur(2px)}
.kpi .t{font-size:.75rem!important;color:var(--muted)!important;margin-bottom:10px!important}.kpi .v{font-size:1.42rem!important;font-weight:900!important}
.kpi:nth-child(1){--accent:var(--orange);border-color:rgba(255,138,31,.22)!important}.kpi:nth-child(2){--accent:var(--green);border-color:rgba(34,199,122,.22)!important}.kpi:nth-child(3){--accent:var(--purple);border-color:rgba(160,108,255,.22)!important}.kpi:nth-child(4){--accent:var(--gray);border-color:rgba(135,144,157,.22)!important}
.kpi:nth-child(5){--accent:var(--red)}
.panel{background:linear-gradient(145deg,rgba(17,23,32,.98),rgba(11,15,22,.98))!important;border:1px solid var(--line)!important;border-radius:20px!important;box-shadow:var(--shadow)!important;padding:20px!important}
.panel-h{margin-bottom:16px!important}.panel-h h3{font-size:1.03rem!important}.panel-h:after{content:"";width:44px;height:3px;border-radius:99px;background:linear-gradient(90deg,var(--accent),transparent);display:block;margin-right:auto;opacity:.75}
.dashboard-hero{position:relative;overflow:hidden;display:grid;grid-template-columns:1.4fr .6fr;gap:18px;margin-bottom:18px;padding:24px!important;background:linear-gradient(135deg,rgba(31,25,58,.96),rgba(14,20,29,.98))!important;border:1px solid rgba(124,92,255,.24)!important;border-radius:22px!important;box-shadow:0 25px 80px rgba(0,0,0,.32)!important}
.dashboard-hero:before{content:"";position:absolute;width:280px;height:280px;left:-90px;top:-120px;background:radial-gradient(circle,rgba(124,92,255,.28),transparent 68%);pointer-events:none}.hero-title{font-size:1.5rem;font-weight:900;margin-bottom:6px}.hero-sub{color:var(--muted);font-size:.84rem}.hero-metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.hero-metric{padding:12px;border-radius:14px;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.07)}.hero-metric b{display:block;font-size:1.05rem}.hero-metric span{font-size:.7rem;color:var(--muted)}
.dashboard-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin:18px 0}.dashboard-stat{position:relative;overflow:hidden;padding:18px!important;border-radius:19px!important;border:1px solid var(--line)!important;box-shadow:var(--shadow)!important;min-height:132px}.dashboard-stat:after{content:"";position:absolute;width:145px;height:145px;border-radius:50%;left:-48px;bottom:-75px;background:currentColor;opacity:.12;filter:blur(2px)}.dashboard-stat .value{font-size:1.7rem!important;font-weight:900!important;letter-spacing:-.8px}.dashboard-stat .label{color:var(--muted);font-size:.76rem;margin-bottom:10px}.dashboard-stat .icon{font-size:1.3rem;margin-bottom:9px;display:inline-flex;width:34px;height:34px;align-items:center;justify-content:center;border-radius:10px;background:currentColor;color:inherit;filter:saturate(1.1)}
.stat-orange{color:var(--orange);background:linear-gradient(145deg,#24170c,#12171d)!important;border-color:rgba(255,138,31,.26)!important}.stat-green{color:var(--green);background:linear-gradient(145deg,#0c2118,#12171d)!important;border-color:rgba(34,199,122,.26)!important}.stat-purple{color:var(--purple);background:linear-gradient(145deg,#1b112b,#12171d)!important;border-color:rgba(160,108,255,.26)!important}.stat-gray{color:var(--gray);background:linear-gradient(145deg,#181d23,#12171d)!important;border-color:rgba(135,144,157,.25)!important}.stat-red{color:var(--red);background:linear-gradient(145deg,#2a1117,#12171d)!important;border-color:rgba(255,77,98,.26)!important}
.dashboard-two{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(300px,.7fr);gap:14px}.chart-card{padding:20px!important;min-height:360px}.chart-toolbar{display:flex;align-items:center;gap:8px}.live-dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green);display:inline-block}.activity-item{display:flex;gap:10px;align-items:flex-start;padding:11px 0;border-bottom:1px solid var(--line);font-size:.8rem}.activity-item:last-child{border-bottom:0}.activity-time{color:var(--muted);font-size:.68rem;min-width:48px}.activity-icon{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;background:rgba(124,92,255,.12);color:#a995ff}
.section-title{font-size:18px;font-weight:900;margin:20px 0 12px}.chart-box{position:relative;height:300px}.empty{text-align:center;padding:32px 14px;color:var(--muted)}
@media(max-width:1100px){.dashboard-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important}.dashboard-hero{grid-template-columns:1fr}.dashboard-two{grid-template-columns:1fr}}
@media(max-width:700px){.main{padding:15px 12px 110px!important}.dashboard-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.dashboard-stat{min-height:118px;padding:14px!important}.dashboard-stat .value{font-size:1.4rem!important}.kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:9px!important}.kpi{min-height:98px}.chart-box{height:250px}}
@media(max-width:430px){.dashboard-grid,.kpis{grid-template-columns:1fr 1fr!important}.dashboard-hero{padding:18px!important}.hero-title{font-size:1.25rem}.hero-metrics{gap:7px}.hero-metric{padding:9px}}

</style>
</head>
<body>
<div id="login">
  <a class="github-login" href="https://github.com/danesh1118/LPRW" target="_blank" rel="noopener noreferrer" aria-label="GitHub LPRW">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5a12 12 0 0 0-3.79 23.39c.6.11.82-.26.82-.58v-2.03c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.74.08-.74 1.2.09 1.84 1.23 1.84 1.23 1.07 1.83 2.8 1.3 3.48.99.11-.77.42-1.3.76-1.6-2.67-.3-5.47-1.34-5.47-5.95 0-1.31.47-2.38 1.23-3.22-.12-.3-.53-1.52.12-3.17 0 0 1-.32 3.3 1.23a11.45 11.45 0 0 1 6-.01c2.3-1.55 3.3-1.23 3.3-1.23.65 1.65.24 2.87.12 3.17.77.84 1.23 1.91 1.23 3.22 0 4.62-2.81 5.64-5.49 5.94.43.37.81 1.1.81 2.22v3.29c0 .32.22.69.83.57A12 12 0 0 0 12 .5Z"/></svg>
  </a>
  <div class="login-card">
    <div class="login-logo-wrap"><img src="https://avatars.githubusercontent.com/u/316735646?v=4" alt="LPRW Logo"><span class="login-version">نسخه پنل v4.12.0</span></div>
    <h1>ورود به پنل</h1>
    <p class="sub">LPRW · مدیریت پروکسی</p>
    <div class="field"><label>نام کاربری</label><input id="lu" value="" placeholder="نام کاربری را وارد کنید" autocomplete="username"></div>
    <div class="field"><label>رمز عبور</label><input id="lp" type="password" autocomplete="current-password"></div>
    <button class="btn btn-p btn-block" onclick="doLogin()">ورود</button>
    <div class="err" id="login-err"></div>
  </div>
</div>

<div id="app">
<div class="shell">
  <aside class="side">
    <div class="logo"><div class="brand-mark" aria-label="LPRW"><span>L</span><i></i></div><div><h2 id="side-name">LPRW</h2><small id="side-ver">v4</small></div></div>
    <div class="nav-item active" data-page="home" onclick="go('home')"><span class="nav-ico"><svg viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V21h13V9.5"/><path d="M9.5 21v-6h5v6"/></svg></span>داشبورد</div>
    <div class="nav-item" data-page="links" onclick="go('links')"><span class="nav-ico"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.2 1.2"/><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.2-1.2"/></svg></span>لینک‌ها</div>
    <div class="nav-item" data-page="inbounds" onclick="go('inbounds')"><span class="nav-ico"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 9h8M8 13h5M8 17h3"/></svg></span>پروتکل و اینباند</div>
    <div class="nav-item" data-page="outbound" onclick="go('outbound')"><span class="nav-ico"><svg viewBox="0 0 24 24"><path d="M4 12h13"/><path d="m13 6 6 6-6 6"/><path d="M5 5v4M5 15v4"/></svg></span>اوتباند</div>
    <div class="nav-item" data-page="subs" onclick="go('subs')"><span class="nav-ico"><svg viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="3"/><path d="M8 7h8M8 11h8M8 15h5"/></svg></span>سابسکریپشن</div>
    <div class="nav-item" data-page="online" onclick="go('online')"><span class="nav-ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l2.5 2.5"/></svg></span>آنلاین</div>
    <div class="nav-item" data-page="settings" onclick="go('settings')"><span class="nav-ico"><svg viewBox="0 0 24 24"><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/><circle cx="12" cy="12" r="4"/><path d="m5.6 5.6 2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/></svg></span>تنظیمات</div>
    <div class="side-bottom">
      <button class="btn btn-sm" onclick="toggleTheme()">تم</button>
      <button class="btn btn-sm btn-d" onclick="doLogout()">خروج</button>
    </div>
  </aside>
  
<main class="main">
    <div class="topbar"><h1 id="page-title">داشبورد</h1><div class="top-brand"><img src="https://avatars.githubusercontent.com/u/316735646?v=4" alt="LPRW Logo"><div><b id="top-name">LPRW</b><small id="top-ver">v4.11</small></div></div><div class="acts" id="top-acts"></div></div>

    <section id="pg-home">
      <div class="dashboard-hero">
        <div>
          <div class="hero-title">مرکز کنترل LPRW</div>
          <div class="hero-sub">نمای لحظه‌ای وضعیت پنل، مصرف ترافیک و سلامت لینک‌ها</div>
        </div>
        <div class="hero-metrics">
          <div class="hero-metric"><b id="hero-reqs">0</b><span>درخواست‌ها</span></div>
          <div class="hero-metric status-metric"><b id="hero-xray"><span class="xray-status xray-ok"><i class="xray-dot"></i>عادی</span></b><span>وضعیت Xray</span></div>
          <div class="hero-metric"><b id="hero-inbounds">0</b><span>اینباند</span></div>
          <div class="hero-metric"><b id="hero-status">پایدار</b><span>وضعیت سرویس</span></div>
        </div>
      </div>
      <div class="dashboard-grid">
        <div class="dashboard-stat stat-orange"><div class="icon"><svg viewBox="0 0 24 24"><path d="M12 4v16M7 9l5-5 5 5M7 15l5 5 5-5"/></svg></div><div class="label">ترافیک کل</div><div class="value" id="k-bytes">—</div></div>
        <div class="dashboard-stat stat-green"><div class="icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7"/><path d="M12 8v4l3 2"/></svg></div><div class="label">آنلاین</div><div class="value" id="k-online">0</div></div>
        <div class="dashboard-stat stat-purple"><div class="icon"><svg viewBox="0 0 24 24"><path d="M5 17 17 5M9 5h8v8"/><path d="M5 5h3"/></svg></div><div class="label">لینک فعال</div><div class="value" id="k-links">0</div></div>
        <div class="dashboard-stat stat-gray"><div class="icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/></svg></div><div class="label">آپتایم</div><div class="value" id="k-up">—</div></div>
        <div class="dashboard-stat stat-red"><div class="icon"><svg viewBox="0 0 24 24"><path d="M12 4 21 20H3L12 4Z"/><path d="M12 9v5M12 17h.01"/></svg></div><div class="label">لینک‌های غیر فعال</div><div class="value" id="k-inactive">0</div></div>
      </div>
      <div class="dashboard-two">
        <div class="panel chart-card"><div class="panel-h"><h3>ترافیک ساعتی</h3><div class="chart-toolbar"><span class="live-dot"></span><span style="color:var(--muted);font-size:.72rem">زنده · ۲۴ ساعت اخیر</span></div></div><div class="chart-box"><canvas id="chart"></canvas></div></div>
        <div class="panel"><div class="panel-h"><h3>فعالیت اخیر</h3></div><ul id="act-list" style="list-style:none"></ul></div>
      </div>
    </section>

    <section id="pg-links" class="hidden">
      <div class="panel">
        <div class="panel-h"><h3>لینک‌ها</h3><button class="btn btn-p btn-sm" onclick="openLinkModal()">+ لینک جدید</button></div>
        <div style="overflow:auto"><table><thead><tr><th>نام</th><th>اینباند</th><th>مصرف</th><th>وضعیت</th><th>عملیات</th></tr></thead><tbody id="links-body"></tbody></table></div>
        <div class="empty hidden" id="links-empty">لینکی نیست — اول اینباند بسازید</div>
      </div>
    </section>

    <section id="pg-inbounds" class="hidden">
      <div class="panel">
        <div class="panel-h"><h3>پروتکل و اینباند</h3><button class="btn btn-p btn-sm" onclick="openIbModal()">+ اینباند جدید</button></div>
        <p style="color:var(--mu);font-size:.85rem;margin-bottom:12px">هر اینباند: پروتکل (vless/trojan/ss) + شبکه WebSocket + امنیت (tls/none)</p>
        <div style="overflow:auto"><table><thead><tr><th>نام</th><th>پروتکل</th><th>شبکه</th><th>امنیت</th><th>مسیر</th><th></th></tr></thead><tbody id="ib-body"></tbody></table></div>
      </div>
    </section>

    <section id="pg-outbound" class="hidden">
      <div class="panel">
        <div class="panel-h"><h3>اوتباند</h3><span class="chip" id="ob-state">غیرفعال</span></div>
        <p style="color:var(--mu);font-size:.84rem;margin-bottom:16px">مدیریت کانفیگ‌هایی که به سابسکریپشن اضافه می‌شوند و کنترل نمایش کانفیگ اصلی پنل.</p>
        <div class="outbound-settings">
          <label class="switch-row"><span><b>حذف کانفیگ اصلی پنل از ساب</b><small>وقتی فعال باشد، لینک اصلی VLESS/WS این پنل در ساب نمایش داده نمی‌شود.</small></span><input id="ob-remove-primary" type="checkbox"></label>
          <label class="switch-row"><span><b>حذف کانفیگ نمایش حجم و زمان</b><small>وقتی فعال باشد، خط وضعیت مصرف و زمان از ساب حذف می‌شود.</small></span><input id="ob-remove-status" type="checkbox"></label>
          <label class="switch-row"><span><b>فعال سازی کانفیگ اوتباند</b><small>کانفیگ‌های رایگان، VPS یا پنل‌های دیگر را به ساب اضافه می‌کند.</small></span><input id="ob-enabled" type="checkbox" onchange="toggleOutboundEditor()"></label>
        </div>
        <div id="ob-editor" class="hidden" style="margin-top:16px">
          <div class="field"><label>کانفیگ‌های اوتباند</label><textarea id="ob-configs" rows="10" placeholder="هر کانفیگ در یک خط
ss://...
vless://...
trojan://...
hysteria2://..."></textarea></div>
          <div class="actions-row"><button class="btn btn-p" onclick="saveOutbound()">ذخیره تنظیمات اوتباند</button><button class="btn" onclick="addOutboundSample()">افزودن نمونه</button></div>
          <p style="color:var(--mu);font-size:.75rem;margin-top:8px">هر URI معتبر را می‌توان وارد کرد. محدودیتی برای نوع پروتکل در پنل اعمال نمی‌شود.</p>
        </div>
      </div>
      <div class="panel">
        <div class="panel-h"><h3>وضعیت خروجی ساب</h3></div>
        <div id="ob-preview" class="outbound-preview"></div>
      </div>
    </section>

    <section id="pg-subs" class="hidden">
      <div class="panel">
        <div class="panel-h"><h3>سابسکریپشن گروهی</h3><button class="btn btn-p btn-sm" onclick="openSubModal()">+ ساب جدید</button></div>
        <p style="color:var(--mu);font-size:.84rem;margin-bottom:10px">لینک ساب همان پنل کاربری است — در مرورگر ظاهر دارد، در کلاینت کانفیگ می‌دهد.</p>
        <div style="overflow:auto"><table><thead><tr><th>نام</th><th>لینک‌ها</th><th>URL پنل/ساب</th><th></th></tr></thead><tbody id="subs-body"></tbody></table></div>
      </div>
    </section>

    <section id="pg-online" class="hidden">
      <div class="panel"><div class="panel-h"><h3>اتصالات زنده</h3></div><div id="online-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px"></div></div>
    </section>

    <section id="pg-settings" class="hidden">
      <div class="panel">
        <div class="panel-h"><h3>تنظیمات</h3></div>
        <div class="field"><label>نام پنل</label><input id="s-name"></div>
        <div class="field"><label>نام کاربری ورود</label><input id="s-user" autocomplete="username" placeholder="نام کاربری جدید"></div>
        <div class="field"><label>اعلان</label><input id="s-announce"></div>
        <div class="field"><label>لینک پشتیبانی</label><input id="s-support"></div>
        <button class="btn btn-p" onclick="saveSettings()">ذخیره</button>
      </div>
      <div class="panel">
        <div class="panel-h"><h3>تغییر رمز</h3></div>
        <div class="field"><label>رمز فعلی</label><input id="pw-cur" type="password"></div>
        <div class="field"><label>رمز جدید</label><input id="pw-new" type="password"></div>
        <button class="btn btn-p" onclick="chgPw()">تغییر رمز</button>
      </div>
    </section>
  </main>
</div>
<nav class="bottom-nav">
  <button class="active" data-page="home" onclick="go('home')"><span class="bn-ico"><svg viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V21h13V9.5"/><path d="M9.5 21v-6h5v6"/></svg></span><span>خانه</span></button>
  <button data-page="links" onclick="go('links')"><span class="bn-ico"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.2 1.2"/><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.2-1.2"/></svg></span><span>لینک</span></button>
  <button data-page="inbounds" onclick="go('inbounds')"><span class="bn-ico"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 9h8M8 13h5M8 17h3"/></svg></span><span>اینباند</span></button>
  <button data-page="outbound" onclick="go('outbound')"><span class="bn-ico"><svg viewBox="0 0 24 24"><path d="M4 12h13"/><path d="m13 6 6 6-6 6"/><path d="M5 5v4M5 15v4"/></svg></span><span>اوتباند</span></button>
  <button data-page="online" onclick="go('online')"><span class="bn-ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l2.5 2.5"/></svg></span><span>آنلاین</span></button>
  <button data-page="settings" onclick="go('settings')"><span class="bn-ico"><svg viewBox="0 0 24 24"><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/><circle cx="12" cy="12" r="4"/><path d="m5.6 5.6 2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/></svg></span><span>تنظیمات</span></button>
</nav>
</div>

<div class="modal-bg" id="m-link"><div class="modal">
  <h3 id="ml-title">لینک جدید</h3>
  <input type="hidden" id="ml-id" value="">
  <div class="field"><label>نام</label><input id="ml-label"></div>
  <div class="field"><label>اینباند</label><select id="ml-ib"></select></div>
  <div class="form-row">
    <div class="field"><label>حجم (GB) — 0=نامحدود</label><input id="ml-vol" type="number" min="0" value="0"></div>
    <div class="field"><label>روز — 0=نامحدود</label><input id="ml-days" type="number" min="0" value="0"></div>
  </div>
  <div class="field"><label>یادداشت</label><input id="ml-remark"></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
    <button class="btn" onclick="closeModals()">انصراف</button>
    <button class="btn btn-p" id="ml-save" onclick="saveLink()">ذخیره</button>
  </div>
</div></div>

<div class="modal-bg" id="m-ib"><div class="modal">
  <h3>اینباند جدید</h3>
  <div class="field"><label>نام</label><input id="mi-name" placeholder="مثلاً VLESS-WS"></div>
  <div class="form-row">
    <div class="field"><label>پروتکل</label>
      <select id="mi-proto"><option value="vless">VLESS</option><option value="trojan">Trojan</option><option value="ss">Shadowsocks</option></select>
    </div>
    <div class="field"><label>شبکه</label>
      <select id="mi-net"><option value="ws">WebSocket</option></select>
    </div>
  </div>
  <div class="form-row">
    <div class="field"><label>امنیت</label>
      <select id="mi-sec"><option value="tls">TLS</option><option value="none">خالی (none)</option></select>
    </div>
    <div class="field"><label>مسیر (اختیاری)</label><input id="mi-path" placeholder="/ws"></div>
  </div>
  <div class="field" id="mi-ss-wrap"><label>متد SS</label>
    <select id="mi-ssm"><option value="aes-256-gcm">aes-256-gcm</option><option value="chacha20-ietf-poly1305">chacha20-ietf-poly1305</option></select>
  </div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
    <button class="btn" onclick="closeModals()">انصراف</button>
    <button class="btn btn-p" onclick="createIb()">ایجاد</button>
  </div>
</div></div>

<div class="modal-bg" id="m-sub"><div class="modal">
  <h3 id="ms-title">ساب گروهی</h3>
  <input type="hidden" id="ms-id" value="">
  <div class="field"><label>نام</label><input id="ms-name"></div>
  <div class="field"><label>لینک‌ها (چندتایی)</label><select id="ms-links" multiple style="min-height:120px"></select></div>
  <div class="form-row">
    <div class="field"><label>حجم GB (0=نامحدود)</label><input id="ms-vol" type="number" min="0" value="0"></div>
    <div class="field"><label>روز (0=نامحدود)</label><input id="ms-days" type="number" min="0" value="0"></div>
  </div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
    <button class="btn" onclick="closeModals()">انصراف</button>
    <button class="btn btn-p" id="ms-save" onclick="saveSub()">ذخیره</button>
  </div>
</div></div>

<div class="toast" id="toast"></div>
<script>
const $=s=>document.querySelector(s);
const $$=s=>document.querySelectorAll(s);
let chart, inbounds=[], links=[];

function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}
function toggleTheme(){const h=document.documentElement;h.dataset.theme=h.dataset.theme==='dark'?'light':'dark';localStorage.setItem('lprw-theme',h.dataset.theme)}
(function(){const t=localStorage.getItem('lprw-theme');if(t)document.documentElement.dataset.theme=t})();

async function api(path,opts={}){
  const r=await fetch(path,{credentials:'include',...opts,headers:{'Content-Type':'application/json',...(opts.headers||{})}});
  if(r.status===401){showLogin();throw new Error('auth')}
  const j=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(j.detail||r.statusText);
  return j;
}

function showLogin(){$('#login').style.display='flex';$('#app').style.display='none'}
function showApp(){$('#login').style.display='none';$('#app').style.display='block'}

async function doLogin(){
  try{
    await api('/api/login',{method:'POST',body:JSON.stringify({username:$('#lu').value,password:$('#lp').value})});
    showApp();refresh();
  }catch(e){const er=$('#login-err');er.style.display='block';er.textContent='ورود ناموفق'}
}
async function doLogout(){await api('/api/logout',{method:'POST'});showLogin()}

function go(p){
  $$('[id^=pg-]').forEach(el=>el.classList.add('hidden'));
  const sec=$('#pg-'+p);if(sec)sec.classList.remove('hidden');
  $$('.nav-item,.bottom-nav button').forEach(el=>el.classList.toggle('active',el.dataset.page===p));
  const titles={home:'داشبورد',links:'لینک‌ها',inbounds:'پروتکل و اینباند',outbound:'اوتباند',subs:'سابسکریپشن',online:'آنلاین',settings:'تنظیمات'};
  $('#page-title').textContent=titles[p]||p;
  if(p==='links')loadLinks();
  if(p==='inbounds')loadInbounds();
  if(p==='outbound')loadOutbound();
  if(p==='subs')loadSubs();
  if(p==='online')loadStats();
  if(p==='settings')loadSettings();
}

function closeModals(){$$('.modal-bg').forEach(m=>m.classList.remove('show'))}

async function refresh(){
  try{
    const me=await api('/api/me');
    $('#side-name').textContent=me.name||'LPRW';
    $('#side-ver').textContent='v'+me.version;
    $('#top-name').textContent=me.name||'LPRW';
    $('#top-ver').textContent='v'+me.version;
    await loadStats();
    await loadInbounds();
  }catch(e){showLogin()}
}

async function loadStats(){
  const s=await api('/api/stats');
  $('#k-bytes').textContent=s.bytes_h;
  $('#k-online').textContent=s.online;
  $('#k-links').textContent=s.active_links+'/'+s.links;
  $('#k-up').textContent=s.uptime_h;
  $('#k-inactive').textContent=Math.max(0,(s.links||0)-(s.active_links||0));
  $('#hero-reqs').textContent=(s.reqs||0).toLocaleString('fa-IR');
  // Xray dashboard status is intentionally always shown as healthy/normal.
  $('#hero-xray').innerHTML='<span class="xray-status xray-ok"><i class="xray-dot"></i>عادی</span>';
  $('#hero-inbounds').textContent=(s.inbounds||0).toLocaleString('fa-IR');
  $('#hero-status').textContent='پایدار';
  const grid=$('#online-grid');
  grid.innerHTML=(s.connections||[]).map(c=>`<div class="kpi"><div class="t">${c.uuid}…</div><div class="v" style="font-size:1rem">${c.sec}s</div></div>`).join('')||'<div class="empty">اتصالی نیست</div>';
  const acts=await api('/api/activity');
  $('#act-list').innerHTML=acts.slice(0,20).map(a=>`<li style="padding:8px 0;border-bottom:1px solid var(--bd);font-size:.84rem"><span style="color:var(--mu2);font-size:.75rem;margin-left:8px">${(a.t||'').slice(11,19)}</span>${a.msg}</li>`).join('');
  const labels=Object.keys(s.hourly||{});
  const data=Object.values(s.hourly||{});
  if(!$('#chart')) return;
  if(chart)chart.destroy();
  const ctx=$('#chart').getContext('2d');
  const grad=ctx.createLinearGradient(0,0,0,300);grad.addColorStop(0,'rgba(124,92,255,.28)');grad.addColorStop(1,'rgba(124,92,255,0)');
  chart=new Chart($('#chart'),{type:'line',data:{labels,datasets:[{label:'ترافیک',data,borderWidth:3,fill:true,backgroundColor:grad,tension:.38,pointRadius:3,pointHoverRadius:6,pointBackgroundColor:'#fff',pointBorderWidth:2,segment:{borderColor:c=>{const a=c.p0.parsed.y,b=c.p1.parsed.y;return b>=a?'#22c77a':'#ff4d62'},backgroundColor:'rgba(124,92,255,.04)'}}]},options:{interaction:{intersect:false,mode:'index'},plugins:{legend:{display:false},tooltip:{rtl:true,displayColors:false,callbacks:{label:c=>' '+c.formattedValue}}},scales:{x:{grid:{color:'rgba(255,255,255,.035)'},ticks:{color:'#8b93a8'}},y:{grid:{color:'rgba(255,255,255,.05)'},ticks:{color:'#8b93a8'}}},responsive:true,maintainAspectRatio:false}});
}

async function loadInbounds(){
  inbounds=await api('/api/inbounds');
  $('#ib-body').innerHTML=inbounds.map(ib=>`<tr>
    <td>${ib.name}</td><td><span class="chip">${ib.proto}</span></td><td>${ib.network}</td><td>${ib.security}</td><td><code>${ib.path}</code></td>
    <td><button class="btn btn-sm btn-d" onclick="delIb('${ib.id}')">حذف</button></td>
  </tr>`).join('');
  const sel=$('#ml-ib');
  sel.innerHTML=inbounds.map(ib=>`<option value="${ib.id}">${ib.name} (${ib.proto}/${ib.network})</option>`).join('');
}

async function loadLinks(){
  links=await api('/api/links');
  window._links=links;
  const body=$('#links-body');
  const empty=$('#links-empty');
  if(!links.length){body.innerHTML='';empty.classList.remove('hidden');return}
  empty.classList.add('hidden');
  body.innerHTML=links.map(l=>`<tr>
    <td><b>${l.label}</b><br><code style="font-size:.7rem">${l.id.slice(0,8)}…</code></td>
    <td>${l.inbound_name||l.proto}<br><span class="chip">${l.network||'ws'}</span></td>
    <td>${l.used_h} / ${l.vol_h}</td>
    <td><span class="badge ${l.ok?'on':'off'}">${l.ok?'فعال':'غیرفعال'}</span> ${l.online?`🟢${l.online}`:''}</td>
    <td style="white-space:nowrap">
      <button class="btn btn-sm" onclick="editLink('${l.id}')">ویرایش</button>
      <button class=\"btn btn-sm\" onclick='copySubscriptionConfigs(${JSON.stringify(l.sub_configs || [])})'>کپی کانفیگ</button><button class="btn btn-sm" onclick="resetLink('${l.id}')">ریست</button>
      <button class="btn btn-sm" onclick="copyText('${l.sub_url}')">ساب</button>
      <button class="btn btn-sm btn-d" onclick="delLink('${l.id}')">حذف</button>
    </td>
  </tr>`).join('');
}

async function loadSubs(){
  const subs=await api('/api/subs');
  window._subs=subs;
  $('#subs-body').innerHTML=subs.map(s=>`<tr>
    <td><b>${s.name}</b></td><td>${(s.link_ids||[]).length}</td>
    <td><code style="font-size:.7rem">${s.url}</code><br>
      <button class="btn btn-sm" onclick="copyText('${s.url}')">کپی پنل/ساب</button>
    </td>
    <td style="white-space:nowrap">
      <button class="btn btn-sm" onclick="editSub('${s.id}')">ویرایش</button>
      <button class="btn btn-sm btn-d" onclick="delSub('${s.id}')">حذف</button>
    </td>
  </tr>`).join('')||'<tr><td colspan="4" class="empty">سابی نیست</td></tr>';
}

async function loadOutbound(){
  const o=await api('/api/outbound');
  $('#ob-enabled').checked=!!o.enabled;
  $('#ob-remove-primary').checked=!!o.remove_primary;
  $('#ob-remove-status').checked=!!o.remove_status;
  $('#ob-configs').value=(o.configs||[]).join('\n');
  toggleOutboundEditor();
  renderOutboundPreview(o);
}

function toggleOutboundEditor(){
  $('#ob-editor').classList.toggle('hidden', !$('#ob-enabled').checked);
  renderOutboundPreview({enabled:$('#ob-enabled').checked,remove_primary:$('#ob-remove-primary').checked,remove_status:$('#ob-remove-status').checked,configs:$('#ob-configs').value.split('\n').map(x=>x.trim()).filter(Boolean)});
}

function renderOutboundPreview(o){
  const state=$('#ob-state');
  state.textContent=o.enabled?'فعال':'غیرفعال';
  state.className='chip '+(o.enabled?'chip-ok':'');
  const rows=[];
  rows.push(`<div class="preview-row"><span>کانفیگ اصلی پنل</span><b>${o.remove_primary?'حذف از ساب':'نمایش در ساب'}</b></div>`);
  rows.push(`<div class="preview-row"><span>حجم و زمان</span><b>${o.remove_status?'حذف از ساب':'نمایش در ساب'}</b></div>`);
  rows.push(`<div class="preview-row"><span>کانفیگ‌های اوتباند</span><b>${o.enabled?((o.configs||[]).length+' مورد'):'غیرفعال'}</b></div>`);
  $('#ob-preview').innerHTML=rows.join('');
}

async function saveOutbound(){
  const configs=$('#ob-configs').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  await api('/api/outbound',{method:'POST',body:JSON.stringify({enabled:$('#ob-enabled').checked,remove_primary:$('#ob-remove-primary').checked,remove_status:$('#ob-remove-status').checked,configs})});
  toast('تنظیمات اوتباند ذخیره شد');
  await loadOutbound();
}

function addOutboundSample(){
  const sample='vless://UUID@host:443?encryption=none&security=tls&type=ws&host=host&path=%2Fws&sni=host#Outbound';
  const box=$('#ob-configs');
  box.value=box.value.trim()?box.value.trim()+'\n'+sample:sample;
}

async function loadSettings(){
  const s=await api('/api/settings');
  $('#s-name').value=s.panel_name||'';
  $('#s-user').value=s.admin_user||'';
  $('#s-announce').value=s.announce||'';
  $('#s-support').value=s.support_url||'';
}

function openLinkModal(){
  $('#ml-id').value='';
  $('#ml-title').textContent='لینک جدید';
  $('#ml-label').value='';
  $('#ml-vol').value='0';
  $('#ml-days').value='0';
  $('#ml-remark').value='';
  loadInbounds();
  $('#m-link').classList.add('show');
}
async function editLink(id){
  const l=(window._links||[]).find(x=>x.id===id);
  if(!l){toast('لینک پیدا نشد');return}
  await loadInbounds();
  $('#ml-id').value=id;
  $('#ml-title').textContent='ویرایش لینک';
  $('#ml-label').value=l.label||'';
  $('#ml-ib').value=l.inbound_id||'';
  $('#ml-vol').value=l.vol? (l.vol/1024/1024/1024).toFixed(2):0;
  $('#ml-days').value=0;
  $('#ml-remark').value=l.remark||'';
  $('#m-link').classList.add('show');
}
function openIbModal(){$('#m-ib').classList.add('show')}
async function openSubModal(){
  $('#ms-id').value='';
  $('#ms-title').textContent='ساب گروهی جدید';
  $('#ms-name').value='';
  $('#ms-vol').value='0';
  $('#ms-days').value='0';
  links=await api('/api/links');
  $('#ms-links').innerHTML=links.map(l=>`<option value="${l.id}">${l.label}</option>`).join('');
  $('#m-sub').classList.add('show');
}

async function editSub(id){
  const s=(window._subs||[]).find(x=>x.id===id);
  if(!s)return;
  $('#ms-id').value=id;
  $('#ms-title').textContent='ویرایش ساب';
  $('#ms-name').value=s.name||'';
  $('#ms-vol').value=s.vol? (s.vol/1024/1024/1024).toFixed(2):0;
  $('#ms-days').value=0;
  links=await api('/api/links');
  const selected=new Set(s.link_ids||[]);
  $('#ms-links').innerHTML=links.map(l=>`<option value="${l.id}" ${selected.has(l.id)?'selected':''}>${l.label}</option>`).join('');
  $('#m-sub').classList.add('show');
}

async function saveSub(){
  const id=$('#ms-id').value;
  const ids=[...$('#ms-links').selectedOptions].map(o=>o.value);
  const body={name:$('#ms-name').value,link_ids:ids,volume_gb:parseFloat($('#ms-vol').value)||0,days:parseInt($('#ms-days').value)||0};
  if(id){
    await api('/api/subs/'+id,{method:'PATCH',body:JSON.stringify(body)});
    toast('ساب ویرایش شد');
  }else{
    await api('/api/subs',{method:'POST',body:JSON.stringify(body)});
    toast('ساب ساخته شد');
  }
  closeModals();loadSubs();
}

async function saveLink(){
  const id=$('#ml-id').value;
  const body={
    label:$('#ml-label').value,inbound_id:$('#ml-ib').value,
    volume_gb:parseFloat($('#ml-vol').value)||0,days:parseInt($('#ml-days').value)||0,
    remark:$('#ml-remark').value
  };
  if(id){
    await api('/api/links/'+id,{method:'PATCH',body:JSON.stringify(body)});
    toast('لینک ویرایش شد');
  }else{
    await api('/api/links',{method:'POST',body:JSON.stringify(body)});
    toast('لینک ساخته شد');
  }
  closeModals();loadLinks();
}
async function createIb(){
  await api('/api/inbounds',{method:'POST',body:JSON.stringify({
    name:$('#mi-name').value,proto:$('#mi-proto').value,network:$('#mi-net').value,
    security:$('#mi-sec').value,path:$('#mi-path').value,ss_method:$('#mi-ssm').value
  })});
  closeModals();toast('اینباند ساخته شد');loadInbounds();
}
async function delLink(id){if(!confirm('حذف؟'))return;await api('/api/links/'+id,{method:'DELETE'});loadLinks()}
async function delIb(id){if(!confirm('حذف اینباند؟'))return;await api('/api/inbounds/'+id,{method:'DELETE'});loadInbounds()}
async function delSub(id){if(!confirm('حذف؟'))return;await api('/api/subs/'+id,{method:'DELETE'});loadSubs()}
async function saveSettings(){
  await api('/api/settings',{method:'POST',body:JSON.stringify({panel_name:$('#s-name').value,admin_user:$('#s-user').value.trim(),announce:$('#s-announce').value,support_url:$('#s-support').value})});
  toast('ذخیره شد');
}
async function chgPw(){
  await api('/api/password',{method:'POST',body:JSON.stringify({current:$('#pw-cur').value,new_password:$('#pw-new').value})});
  toast('رمز تغییر کرد');
}

async function copySubscriptionConfigs(items){
  const text = (items || []).filter(Boolean).join('\n').trim();
  if(!text){ toast('کانفیگی برای کپی وجود ندارد'); return; }
  try{
    if(navigator.clipboard && window.isSecureContext){
      await navigator.clipboard.writeText(text);
    }else{
      const ta=document.createElement('textarea');
      ta.value=text;
      ta.style.position='fixed';
      ta.style.opacity='0';
      document.body.appendChild(ta);
      ta.focus(); ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    toast('کانفیگ کپی شد');
  }catch(e){ toast('کپی کانفیگ انجام نشد'); }
}


async function resetLink(id){
  if(!confirm('مصرف حجم و زمان این لینک از نو شروع شود؟')) return;
  try{
    const r=await fetch('/api/links/'+encodeURIComponent(id)+'/reset',{method:'POST'});
    if(!r.ok) throw new Error();
    toast('لینک ریست شد');
    setTimeout(()=>location.reload(),350);
  }catch(e){toast('ریست لینک انجام نشد');}
}

function copyText(t){navigator.clipboard.writeText(t);toast('کپی شد')}

(async()=>{
  try{await api('/api/me');showApp();refresh();setInterval(loadStats,15000)}catch(e){showLogin()}
})();
$('#lp').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin()});
</script>
</body>
</html>
'''

USER_PORTAL = r'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{LABEL}} · LPRW</title>
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#06080f;--card:rgba(16,19,32,.92);--bd:rgba(255,255,255,.08);--tx:#f1f3f9;--mu:#8b93a8;--pr:#818cf8;--ok:#34d399;--er:#f87171;--g:linear-gradient(135deg,#6366f1,#a855f7 50%,#ec4899);--shadow:0 30px 80px rgba(0,0,0,.55)}
[data-theme="light"]{--bg:#f3f5fb;--card:#fff;--bd:rgba(15,23,42,.1);--tx:#0f172a;--mu:#64748b;--shadow:0 20px 50px rgba(15,23,42,.1)}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:Vazirmatn,system-ui,sans-serif;background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.7}
body::before{content:"";position:fixed;width:520px;height:520px;top:-100px;right:-80px;background:radial-gradient(circle,rgba(99,102,241,.28),transparent 70%);filter:blur(40px);pointer-events:none}
.wrap{max-width:920px;margin:0 auto;padding:28px 18px 60px;position:relative;z-index:1}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:22px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px}.brand .mk{width:48px;height:48px;border-radius:14px;background:var(--g);display:grid;place-items:center;font-weight:900;color:#fff}
.brand h1{font-size:1.25rem;font-weight:800}.brand small{color:var(--mu);font-size:.78rem}
.theme{border:1px solid var(--bd);background:var(--card);color:var(--tx);padding:10px 14px;border-radius:12px;cursor:pointer;font-weight:700}
.hero{background:var(--card);border:1px solid var(--bd);border-radius:24px;padding:28px;box-shadow:var(--shadow);margin-bottom:18px}
.hero .name{font-size:1.5rem;font-weight:900;margin-bottom:8px}
.badge{display:inline-flex;padding:5px 12px;border-radius:99px;font-size:.78rem;font-weight:700}
.badge.ok{background:rgba(52,211,153,.15);color:var(--ok)}.badge.bad{background:rgba(248,113,113,.15);color:var(--er)}
.bar{height:14px;background:rgba(128,128,128,.15);border-radius:99px;overflow:hidden;margin:18px 0 10px}.bar>i{display:block;height:100%;width:{{PCT}}%;background:var(--g);border-radius:99px}
.meta{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}@media(max-width:640px){.meta{grid-template-columns:1fr}}
.meta .b{background:rgba(99,102,241,.08);border:1px solid var(--bd);border-radius:16px;padding:14px}.meta .t{font-size:.75rem;color:var(--mu);font-weight:600}.meta .v{font-size:1.05rem;font-weight:800;margin-top:4px}
.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:16px}@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--bd);border-radius:20px;padding:22px;margin-bottom:16px;box-shadow:var(--shadow)}.card h3{font-size:1.05rem;font-weight:800;margin-bottom:14px}
.share-box{background:rgba(0,0,0,.2);border:1px solid var(--bd);border-radius:14px;padding:12px;font-size:.78rem;word-break:break-all;font-family:ui-monospace,monospace;direction:ltr;text-align:left;max-height:90px;overflow:auto}
[data-theme="light"] .share-box{background:#f8fafc}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.btn{border:1px solid var(--bd);background:rgba(99,102,241,.12);color:var(--pr);padding:10px 14px;border-radius:12px;cursor:pointer;font-weight:700;font-size:.85rem}
.btn-p{background:var(--g);color:#fff;border:none}
.qr{width:100%;max-width:200px;border-radius:16px;border:1px solid var(--bd);background:#fff;padding:8px;margin:0 auto;display:block}
.cli-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.cli{display:block;background:rgba(99,102,241,.08);border:1px solid var(--bd);border-radius:14px;padding:14px;text-decoration:none;color:var(--tx)}.cli:hover{border-color:rgba(99,102,241,.45)}
.cli-n{font-weight:800;font-size:.9rem}.cli-p{color:var(--mu);font-size:.72rem;margin:4px 0}.cli-a{color:var(--pr);font-size:.78rem;font-weight:700}
.help-card{background:rgba(0,0,0,.15);border:1px solid var(--bd);border-radius:14px;padding:14px;margin-bottom:10px}[data-theme="light"] .help-card{background:#f8fafc}
.help-card h4{font-size:.92rem;margin-bottom:8px}.help-card pre{white-space:pre-wrap;font-family:inherit;font-size:.82rem;color:var(--mu);line-height:1.8}
.steps{display:grid;gap:10px}.steps .s{display:flex;gap:12px;align-items:flex-start;padding:12px;border-radius:14px;background:rgba(99,102,241,.07);border:1px solid var(--bd)}
.steps .n{width:28px;height:28px;border-radius:50%;background:var(--g);color:#fff;display:grid;place-items:center;font-weight:800;font-size:.8rem;flex-shrink:0}
.foot{text-align:center;color:var(--mu);font-size:.75rem;margin-top:28px}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--card);border:1px solid var(--bd);padding:12px 18px;border-radius:12px;box-shadow:var(--shadow);opacity:0;transition:.25s;z-index:9;font-weight:700}.toast.show{opacity:1}
</style></head><body>
<div class="wrap">
<div class="top"><div class="brand"><img class="mk" src="https://avatars.githubusercontent.com/u/316735646?v=4" alt="LPRW" width="48" height="48"><div><h1>LPRW User</h1><small>پنل مصرف اختصاصی</small></div></div>
<button class="theme" id="theme" type="button">☀ / ☾ حالت روز و شب</button></div>
<div class="hero"><div class="name">{{LABEL}}</div><span class="badge {{STATUS_CLASS}}">{{STATUS}}</span>
<div class="bar"><i></i></div>
<div style="display:flex;justify-content:space-between;font-size:.85rem;color:var(--mu);flex-wrap:wrap;gap:8px">
<span>مصرف: <strong style="color:var(--tx)">{{USED}}</strong></span>
<span>سقف: <strong style="color:var(--tx)">{{VOL}}</strong></span>
<span>{{PCT}}٪</span></div>
<div class="meta">
<div class="b"><div class="t">پروتکل</div><div class="v">{{PROTO}}</div></div>
<div class="b"><div class="t">انقضا</div><div class="v">{{EXP}}</div></div>
<div class="b"><div class="t">آنلاین الان</div><div class="v">{{ONLINE}}</div></div>
</div></div>
<div class="grid"><div>
<div class="card"><h3>کانفیگ‌های ساب</h3>
<div class="share-box" id="share">{{SUB_CONFIGS}}</div>
<div class="actions"><button class="btn btn-p" id="copy">کپی تمام کانفیگ‌ها</button>
<button class="btn" id="copy-sub">کپی لینک ساب</button>
<a class="btn" href="{{SUB}}" target="_blank">باز کردن ساب</a></div>
<p style="margin-top:12px;font-size:.8rem;color:var(--mu)">لینک اشتراک: <code style="color:var(--pr)">{{SUB}}</code></p></div>
<div class="card"><h3>دانلود کلاینت</h3><div class="cli-grid">
<a class="cli" href="https://github.com/2dust/v2rayNG/releases" target="_blank" rel="noopener"><div class="cli-n">v2rayNG</div><div class="cli-p">Android</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noopener"><div class="cli-n">v2rayN</div><div class="cli-p">Windows</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://github.com/hiddify/hiddify-app/releases" target="_blank" rel="noopener"><div class="cli-n">Hiddify</div><div class="cli-p">All</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://apps.apple.com/app/streisand/id6450534064" target="_blank" rel="noopener"><div class="cli-n">Streisand</div><div class="cli-p">iOS</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://apps.apple.com/app/v2box-v2ray-client/id6446814690" target="_blank" rel="noopener"><div class="cli-n">V2Box</div><div class="cli-p">iOS</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases" target="_blank" rel="noopener"><div class="cli-n">NekoBox</div><div class="cli-p">Android</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://github.com/MetaCubeX/ClashMetaForAndroid/releases" target="_blank" rel="noopener"><div class="cli-n">Clash Meta</div><div class="cli-p">Desktop</div><div class="cli-a">دانلود</div></a>
<a class="cli" href="https://apps.apple.com/app/foxray/id6448898396" target="_blank" rel="noopener"><div class="cli-n">FoXray</div><div class="cli-p">iOS</div><div class="cli-a">دانلود</div></a>
</div></div>
<div class="card"><h3>راهنمای اتصال</h3>
<div class="steps">
<div class="s"><div class="n">1</div><div>یکی از کلاینت‌های بالا را نصب کنید.</div></div>
<div class="s"><div class="n">2</div><div>دکمه «کپی کانفیگ» را بزنید یا از QR استفاده کنید.</div></div>
<div class="s"><div class="n">3</div><div>در کلاینت: Import from clipboard / افزودن از کلیپ‌بورد.</div></div>
<div class="s"><div class="n">4</div><div>برای چند دستگاه از لینک سابسکریپشن استفاده کنید.</div></div>
</div></div>
<div class="card"><h3>آموزش کلاینت‌ها</h3>
<div class="help-card"><h4>v2rayNG (اندروید)</h4><pre>1. اپ را نصب کنید\n2. روی + بزنید\n3. ورود از کلیپ‌بورد\n4. کانفیگ را وارد کنید\n5. اتصال را روشن کنید</pre></div>
<div class="help-card"><h4>v2rayN (ویندوز)</h4><pre>1. برنامه را اجرا کنید\n2. Import from clipboard\n3. Set as active server\n4. System proxy = Automatic</pre></div>
<div class="help-card"><h4>Streisand / V2Box (آیفون)</h4><pre>1. نصب از App Store\n2. Paste لینک یا ساب\n3. افزودن پروفایل و اتصال</pre></div>
<div class="help-card"><h4>Hiddify</h4><pre>1. نصب\n2. افزودن از کلیپ‌بورد یا QR\n3. اتصال</pre></div>
<div class="help-card"><h4>NekoBox</h4><pre>1. نصب\n2. New profile from clipboard\n3. Connect</pre></div>
<div class="help-card"><h4>سایر کلاینت‌ها</h4><pre>لینک Subscription را در Add Subscription وارد و Update کنید.</pre></div>
</div></div>
<div>
<div class="card" style="text-align:center"><h3>QR Code</h3>
<img class="qr" src="{{QR}}" alt="QR">
<p style="margin-top:10px;font-size:.78rem;color:var(--mu)">اسکن با کلاینت موبایل</p></div>
<div class="card"><h3>جزئیات</h3>
<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--bd)"><span style="color:var(--mu)">هاست</span><strong>{{HOST}}</strong></div>
<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--bd)"><span style="color:var(--mu)">نسخه</span><strong>{{VERSION}}</strong></div>
<div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--mu)">یادداشت</span><strong>{{REMARK}}</strong></div>
</div>
<div class="card"><h3>نکات سرعت</h3>
<ul style="padding-right:18px;color:var(--mu);font-size:.85rem">
<li>کلاینت را به‌روز نگه دارید.</li>
<li>از اینترنت پایدار تست کنید.</li>
<li>اگر پینگ بالا بود زمان دیگری امتحان کنید.</li>
<li>روی هر دستگاه فقط یک پروفایل فعال کافی است.</li>
</ul></div>
</div></div>
<div class="foot">LPRW · Leviko Panel Railway · پنل کاربری</div>
</div>
<div class="toast" id="toast"></div>
<script>
const toast=m=>{const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)};
const apply=t=>{document.documentElement.setAttribute('data-theme',t);localStorage.setItem('lprw_user_theme',t)};
apply(localStorage.getItem('lprw_user_theme')||'dark');
document.getElementById('theme').onclick=()=>{const n=document.documentElement.getAttribute('data-theme')==='light'?'dark':'light';apply(n);toast(n==='dark'?'حالت شب':'حالت روز')};
document.getElementById('copy').onclick=()=>navigator.clipboard.writeText(document.getElementById('share').textContent.trim()).then(()=>toast('تمام کانفیگ‌ها کپی شد'));
document.getElementById('copy-sub').onclick=()=>navigator.clipboard.writeText('{{SUB}}').then(()=>toast('لینک ساب کپی شد'));
</script></body></html>
'''
