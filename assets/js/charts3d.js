/* ============================================================
   Lin Project Radar — charts3d.js
   Pure-canvas 3D chart renderers for Cat 1 module deep-dive panels.
   Exposes window.LinCharts3D with 12 renderer functions + wireChart3d.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 3D helpers ---------- */
  function rX(p,a){return{x:p.x,y:p.y*Math.cos(a)-p.z*Math.sin(a),z:p.y*Math.sin(a)+p.z*Math.cos(a)};}
  function rY(p,a){return{x:p.x*Math.cos(a)+p.z*Math.sin(a),y:p.y,z:-p.x*Math.sin(a)+p.z*Math.cos(a)};}
  function proj(p,fov,cx,cy){
    var z=p.z+fov; if(z<1)z=1;
    var s=fov/z;
    var px=cx+p.x*s, py=cy+p.y*s;
    return{x:isFinite(px)?px:cx,y:isFinite(py)?py:cy,s:isFinite(s)?s:1};
  }

  /* ---------- 1.1 Monte Carlo EAC — 3D histogram ---------- */
  function render_histogram3d(ctx, W, H, m, rx, ry) {
    var d=m.data, bac=d.bac, cpi=d.cpi;
    var eacMean=bac/cpi;
    var spread=eacMean*0.08;
    var cx=W/2, cy=H/2+10;
    var fov=Math.min(W,H)*0.8;
    var bars=40;
    var minV=eacMean-spread*1.5, maxV=eacMean+spread*1.5;
    var step=(maxV-minV)/bars;
    function gauss(x,mu,sig){return Math.exp(-0.5*Math.pow((x-mu)/sig,2));}
    var heights=[];
    for(var i=0;i<bars;i++){
      var x=minV+(i+0.5)*step;
      heights.push(gauss(x,eacMean,spread*0.45));
    }
    var maxH=Math.max.apply(null,heights)||1;
    var p50=eacMean, p80=eacMean+spread*0.84;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    for(var g=-5;g<=5;g++){
      var pa=t({x:g*18,y:60,z:-60}),pb=t({x:g*18,y:60,z:60});
      if(!isFinite(pa.x))return;
      ctx.beginPath();ctx.moveTo(pa.x,pa.y);ctx.lineTo(pb.x,pb.y);
      ctx.strokeStyle='rgba(38,52,79,0.4)';ctx.lineWidth=0.5;ctx.stroke();
    }
    for(var g2=-3;g2<=3;g2++){
      var pc=t({x:-90,y:60,z:g2*20}),pd=t({x:90,y:60,z:g2*20});
      if(!isFinite(pc.x))return;
      ctx.beginPath();ctx.moveTo(pc.x,pc.y);ctx.lineTo(pd.x,pd.y);
      ctx.strokeStyle='rgba(38,52,79,0.4)';ctx.lineWidth=0.5;ctx.stroke();
    }
    var bw=4.2, depth=15;
    for(var i=0;i<bars;i++){
      var xpos=(i-bars/2)*bw+bw/2;
      var bh=heights[i]/maxH*100;
      var xv=minV+(i+0.5)*step;
      var isP80=(xv>=p80);
      var col=isP80?'#e0556b':'#4ea0ff';
      var yT=60-bh, yB=60;
      /* jshint ignore:start */
      (function(xp,yt,yb,c3col){
        function c3(dx,dy,dz){return t({x:xp+dx,y:dy,z:dz});}
        var pts=[
          c3(-bw/2,yt,-depth/2),c3(bw/2,yt,-depth/2),
          c3(bw/2,yt,depth/2),c3(-bw/2,yt,depth/2),
          c3(-bw/2,yb,-depth/2),c3(bw/2,yb,-depth/2),
          c3(bw/2,yb,depth/2),c3(-bw/2,yb,depth/2)
        ];
        if(!pts.every(function(p){return isFinite(p.x);})) return;
        function face(idx,alpha){
          ctx.beginPath();ctx.moveTo(pts[idx[0]].x,pts[idx[0]].y);
          idx.forEach(function(j){ctx.lineTo(pts[j].x,pts[j].y);});
          ctx.closePath();ctx.fillStyle=c3col;ctx.globalAlpha=alpha;ctx.fill();
          ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.3;ctx.stroke();
          ctx.globalAlpha=1;
        }
        face([0,1,2,3],0.88);face([4,5,1,0],0.65);face([5,6,2,1],0.45);
      })(xpos,yT,yB,col);
      /* jshint ignore:end */
    }
    var p50idx=Math.round((p50-minV)/step);
    var xp50=(p50idx-bars/2)*bw+bw/2;
    var pl1=t({x:xp50,y:-40,z:-depth/2}),pl2=t({x:xp50,y:60,z:-depth/2});
    if(isFinite(pl1.x)){
      ctx.beginPath();ctx.moveTo(pl1.x,pl1.y);ctx.lineTo(pl2.x,pl2.y);
      ctx.strokeStyle='#3fcaa6';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';ctx.fillText('P50',pl1.x+3,pl1.y);
    }
    var p80idx=Math.round((p80-minV)/step);
    var xp80=(p80idx-bars/2)*bw+bw/2;
    var pl3=t({x:xp80,y:-40,z:-depth/2}),pl4=t({x:xp80,y:60,z:-depth/2});
    if(isFinite(pl3.x)){
      ctx.beginPath();ctx.moveTo(pl3.x,pl3.y);ctx.lineTo(pl4.x,pl4.y);
      ctx.strokeStyle='#e0556b';ctx.lineWidth=1.5;ctx.stroke();
      ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('P80',pl3.x+3,pl3.y);
    }
  }

  /* ---------- 1.2 CUSUM — 3D line + breach marker ---------- */
  function render_cusum3d(ctx, W, H, m, rx, ry) {
    var series=m.data.spiSeries||[1.0];
    var k=0.5, H_limit=4.0;
    var cusum_pos=[0], cusum_neg=[0];
    for(var i=1;i<series.length;i++){
      cusum_pos.push(Math.max(0,cusum_pos[i-1]+(series[i]-1.0)-k));
      cusum_neg.push(Math.min(0,cusum_neg[i-1]+(series[i]-1.0)+k));
    }
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var n=series.length, xSpan=140;
    for(var g=0;g<n;g++){
      var pa=t({x:(g/(n-1)-0.5)*xSpan,y:50,z:-30}),pb=t({x:(g/(n-1)-0.5)*xSpan,y:50,z:30});
      if(!isFinite(pa.x))return;
      ctx.beginPath();ctx.moveTo(pa.x,pa.y);ctx.lineTo(pb.x,pb.y);
      ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();
    }
    for(var i=0;i<series.length-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=50-(series[i]-0.85)/0.25*60, y2=50-(series[i+1]-0.85)/0.25*60;
      var pa2=t({x:x1,y:y1,z:-20}),pb2=t({x:x2,y:y2,z:-20});
      if(!isFinite(pa2.x))continue;
      ctx.beginPath();ctx.moveTo(pa2.x,pa2.y);ctx.lineTo(pb2.x,pb2.y);
      ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1.2;ctx.stroke();
    }
    for(var i=0;i<cusum_pos.length-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=50-cusum_pos[i]/H_limit*60, y2=50-cusum_pos[i+1]/H_limit*60;
      var pa2=t({x:x1,y:y1,z:0}),pb2=t({x:x2,y:y2,z:0});
      if(!isFinite(pa2.x))continue;
      ctx.beginPath();ctx.moveTo(pa2.x,pa2.y);ctx.lineTo(pb2.x,pb2.y);
      ctx.strokeStyle='#e2b13c';ctx.lineWidth=2;ctx.stroke();
    }
    var dl_y=50-60;
    var dpa=t({x:-xSpan/2,y:dl_y,z:-25}),dpb=t({x:xSpan/2,y:dl_y,z:-25});
    if(isFinite(dpa.x)){
      ctx.beginPath();ctx.moveTo(dpa.x,dpa.y);ctx.lineTo(dpb.x,dpb.y);
      ctx.strokeStyle='#e0556b';ctx.lineWidth=1;ctx.setLineDash([5,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
      ctx.fillText('H=4.0 (limit)',dpa.x,dpa.y-4);
    }
    var lastCusum=cusum_pos[n-1]||0;
    var lastX=((n-1)/(n-1)-0.5)*xSpan;
    var lastY=50-lastCusum/H_limit*60;
    var bp=t({x:lastX,y:lastY,z:0});
    if(isFinite(bp.x)&&lastCusum>=H_limit){
      ctx.beginPath();ctx.arc(bp.x,bp.y,6,0,Math.PI*2);
      ctx.fillStyle='#e0556b';ctx.fill();
      ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
      ctx.fillText('BREACH',bp.x+8,bp.y);
    }
  }

  /* ---------- 1.3 Document Risk — 2D radar spider ---------- */
  function render_risk3d(ctx, W, H, m, rx, ry) {
    ctx.clearRect(0,0,W,H);
    var cx=W/2, cy=H/2+10, R=Math.min(W,H)*0.32;
    var score=m.data.score||0;
    var dims=[
      {label:'RFI Density',   val:Math.min(score*1.2+0.05,1), col:'#e2b13c'},
      {label:'Dispute Lang',  val:Math.min(score*1.5,1),       col:'#e0556b'},
      {label:'Change Orders', val:Math.min(score*0.9+0.03,1),  col:'#e2b13c'},
      {label:'NCR Rate',      val:Math.min(score*0.65,1),       col:'#3fcaa6'},
      {label:'Submittal Rej', val:Math.min(score*0.7+0.05,1),  col:'#3fcaa6'},
      {label:'OAC Issues',    val:Math.min(score*1.3,1),        col:'#e2b13c'}
    ];
    var n=dims.length;
    [0.30,0.70,1.0].forEach(function(thresh,ti){
      var col=['#3fcaa6','#e2b13c','#e0556b'][ti];
      ctx.beginPath();
      for(var i=0;i<=n;i++){
        var a=(i/n)*Math.PI*2-Math.PI/2;
        var r=thresh*R;
        i===0?ctx.moveTo(cx+r*Math.cos(a),cy+r*Math.sin(a)):ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a));
      }
      ctx.closePath();ctx.strokeStyle=col+'55';ctx.lineWidth=0.8;ctx.stroke();
      ctx.fillStyle=col+'08';ctx.fill();
    });
    dims.forEach(function(d2,i){
      var a=(i/n)*Math.PI*2-Math.PI/2;
      ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+R*Math.cos(a),cy+R*Math.sin(a));
      ctx.strokeStyle='rgba(38,52,79,0.7)';ctx.lineWidth=0.7;ctx.stroke();
      var lx=cx+(R+20)*Math.cos(a), ly=cy+(R+20)*Math.sin(a);
      ctx.font='8px SFMono-Regular,monospace';
      var tw=ctx.measureText(d2.label).width+8;
      var px=lx-tw/2, py=ly-7;
      if(ctx.roundRect)ctx.roundRect(px,py,tw,14,3); else ctx.rect(px,py,tw,14);
      ctx.fillStyle=d2.col+'18';ctx.fill();
      ctx.strokeStyle=d2.col+'55';ctx.lineWidth=0.7;ctx.stroke();
      ctx.fillStyle=d2.col;ctx.textAlign='center';ctx.fillText(d2.label,lx,ly+3);ctx.textAlign='left';
    });
    ctx.beginPath();
    dims.forEach(function(d2,i){
      var a=(i/n)*Math.PI*2-Math.PI/2;
      var r=d2.val*R;
      i===0?ctx.moveTo(cx+r*Math.cos(a),cy+r*Math.sin(a)):ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a));
    });
    ctx.closePath();
    var polyCol=score>=0.70?'#e0556b':score>=0.30?'#e2b13c':'#3fcaa6';
    ctx.fillStyle=polyCol+'20';ctx.fill();
    ctx.strokeStyle=polyCol;ctx.lineWidth=1.8;ctx.stroke();
    dims.forEach(function(d2,i){
      var a=(i/n)*Math.PI*2-Math.PI/2;
      var r=d2.val*R;
      var px=cx+r*Math.cos(a), py=cy+r*Math.sin(a);
      ctx.beginPath();ctx.arc(px,py,4,0,Math.PI*2);ctx.fillStyle=d2.col;ctx.fill();
    });
    ctx.textAlign='center';
    ctx.font='bold 13px SFMono-Regular,monospace';ctx.fillStyle=polyCol;
    ctx.fillText(score.toFixed(2),cx,cy+4);
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
    ctx.fillText('risk score',cx,cy+16);
    ctx.textAlign='left';
  }

  /* ---------- 1.4 Bayesian EAC — 3D overlapping distributions ---------- */
  function render_bayesian3d(ctx, W, H, m, rx, ry) {
    var d=m.data;
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var dists=[
      {label:'Prior (RCF)',   mu:d.prior,     sig:d.prior*0.06,    col:'#4ea0ff',z:-25},
      {label:'Likelihood',    mu:d.likelihood, sig:d.likelihood*0.05,col:'#e2b13c',z:0},
      {label:'Posterior',     mu:d.posterior,  sig:d.posterior*0.04, col:'#3fcaa6',z:25}
    ];
    var minV=Math.min(d.bac,d.prior)*0.92, maxV=Math.max(d.prior,d.likelihood)*1.08;
    var range=maxV-minV||1;
    var bars=30, xSpan=130;
    dists.forEach(function(dist){
      function gauss(x){return Math.exp(-0.5*Math.pow((x-dist.mu)/dist.sig,2));}
      var heights=[];
      for(var i=0;i<bars;i++){heights.push(gauss(minV+(i+0.5)*range/bars));}
      var maxH=Math.max.apply(null,heights)||1;
      var bw=xSpan/bars;
      heights.forEach(function(h,i){
        var xpos=(i/bars-0.5)*xSpan+bw/2;
        var bh=h/maxH*70;
        var yT=40-bh, yB=40;
        var depth=8;
        /* jshint ignore:start */
        (function(xp,yt,yb,dc){
          function c3(dx,dy,dz){return t({x:xp+dx,y:dy,z:dc.z+dz});}
          var pts=[
            c3(-bw/2,yt,-depth/2),c3(bw/2,yt,-depth/2),
            c3(bw/2,yt,depth/2),c3(-bw/2,yt,depth/2),
            c3(-bw/2,yb,-depth/2),c3(bw/2,yb,-depth/2),
            c3(bw/2,yb,depth/2),c3(-bw/2,yb,depth/2)
          ];
          if(!pts.every(function(p){return isFinite(p.x);}))return;
          function face(idx,alpha){
            ctx.beginPath();ctx.moveTo(pts[idx[0]].x,pts[idx[0]].y);
            idx.forEach(function(j){ctx.lineTo(pts[j].x,pts[j].y);});
            ctx.closePath();ctx.fillStyle=dc.col;ctx.globalAlpha=alpha*0.75;ctx.fill();
            ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.stroke();
            ctx.globalAlpha=1;
          }
          face([0,1,2,3],0.9);face([4,5,1,0],0.65);face([5,6,2,1],0.45);
        })(xpos,yT,yB,dist);
        /* jshint ignore:end */
      });
      var muIdx=Math.round((dist.mu-minV)/range*bars);
      var lp=t({x:(muIdx/bars-0.5)*xSpan,y:-35,z:dist.z});
      if(isFinite(lp.x)){
        ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=dist.col;
        ctx.textAlign='center';ctx.fillText(dist.label,lp.x,lp.y);ctx.textAlign='left';
      }
    });
  }

  /* ---------- 1.5 Kalman Filter SPI — 3D line + uncertainty band ---------- */
  function render_kalman3d(ctx, W, H, m, rx, ry) {
    var raw=m.data.raw||[1.0], smooth=m.data.smooth||[1.0];
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var n=raw.length,xSpan=130;
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var noise=0.012;
      var pts=[
        t({x:x1,y:50-(raw[i]+noise-0.85)/0.25*70,z:0}),
        t({x:x2,y:50-(raw[i+1]+noise-0.85)/0.25*70,z:0}),
        t({x:x2,y:50-(raw[i+1]-noise-0.85)/0.25*70,z:0}),
        t({x:x1,y:50-(raw[i]-noise-0.85)/0.25*70,z:0})
      ];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);
      pts.forEach(function(p){ctx.lineTo(p.x,p.y);});
      ctx.closePath();ctx.fillStyle='rgba(78,160,255,0.08)';ctx.fill();
    }
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:50-(raw[i]-0.85)/0.25*70,z:15});
      var p2=t({x:x2,y:50-(raw[i+1]-0.85)/0.25*70,z:15});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();
      ctx.setLineDash([]);
    }
    for(var i=0;i<smooth.length-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:50-(smooth[i]-0.85)/0.25*70,z:0});
      var p2=t({x:x2,y:50-(smooth[i+1]-0.85)/0.25*70,z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='#4ea0ff';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#4ea0ff';ctx.fill();
    }
    var bp1=t({x:-xSpan/2,y:50-(1.0-0.85)/0.25*70,z:-20});
    var bp2=t({x:xSpan/2,y:50-(1.0-0.85)/0.25*70,z:-20});
    if(isFinite(bp1.x)){
      ctx.beginPath();ctx.moveTo(bp1.x,bp1.y);ctx.lineTo(bp2.x,bp2.y);
      ctx.strokeStyle='rgba(63,202,166,0.4)';ctx.lineWidth=0.8;ctx.setLineDash([4,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';ctx.fillText('SPI=1.0',bp1.x,bp1.y-3);
    }
  }

  /* ---------- 1.6 ARIMA CPI — 3D line + confidence ribbon ---------- */
  function render_arima3d(ctx, W, H, m, rx, ry) {
    var hist=m.data.history||[1.0], fore=m.data.forecast||[], up=m.data.upper||[], lo=m.data.lower||[];
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var nh=hist.length, nf=fore.length, total=nh+nf, xSpan=130;
    for(var i=0;i<nf;i++){
      var xi=nh+i, xi2=nh+i+1;
      if(xi2>total)continue;
      var x1=(xi/(total-1)-0.5)*xSpan, x2=(xi2/(total-1)-0.5)*xSpan;
      var u1=50-(up[i]-0.88)/0.15*80, l1=50-(lo[i]-0.88)/0.15*80;
      var u2=i+1<nf?50-(up[i+1]-0.88)/0.15*80:u1;
      var l2=i+1<nf?50-(lo[i+1]-0.88)/0.15*80:l1;
      var pts=[t({x:x1,y:u1,z:0}),t({x:x2,y:u2,z:0}),t({x:x2,y:l2,z:0}),t({x:x1,y:l1,z:0})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);
      pts.forEach(function(p){ctx.lineTo(p.x,p.y);});
      ctx.closePath();ctx.fillStyle='rgba(226,177,60,0.12)';ctx.fill();
      ctx.strokeStyle='rgba(226,177,60,0.2)';ctx.lineWidth=0.5;ctx.stroke();
    }
    for(var i=0;i<nh-1;i++){
      var x1=(i/(total-1)-0.5)*xSpan, x2=((i+1)/(total-1)-0.5)*xSpan;
      var p1=t({x:x1,y:50-(hist[i]-0.88)/0.15*80,z:0});
      var p2=t({x:x2,y:50-(hist[i+1]-0.88)/0.15*80,z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='#4ea0ff';ctx.lineWidth=2;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#4ea0ff';ctx.fill();
    }
    var allFore=[hist[nh-1]].concat(fore);
    for(var i=0;i<allFore.length-1;i++){
      var xi=(nh-1+i)/(total-1), xi2=(nh+i)/(total-1);
      var p1=t({x:(xi-0.5)*xSpan,y:50-(allFore[i]-0.88)/0.15*80,z:0});
      var p2=t({x:(xi2-0.5)*xSpan,y:50-(allFore[i+1]-0.88)/0.15*80,z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='#e2b13c';ctx.lineWidth=2;ctx.setLineDash([5,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.beginPath();ctx.arc(p2.x,p2.y,3.5,0,Math.PI*2);ctx.fillStyle='#e2b13c';ctx.fill();
    }
    var dp=t({x:((nh-1)/(total-1)-0.5)*xSpan,y:-50,z:0});
    var dp2=t({x:((nh-1)/(total-1)-0.5)*xSpan,y:50,z:0});
    if(isFinite(dp.x)){
      ctx.beginPath();ctx.moveTo(dp.x,dp.y);ctx.lineTo(dp2.x,dp2.y);
      ctx.strokeStyle='rgba(100,116,139,0.4)';ctx.lineWidth=0.8;ctx.setLineDash([3,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('Forecast →',dp.x+4,dp.y+10);
    }
  }

  /* ---------- 1.7 Earned Schedule — 3D dual S-curves ---------- */
  function render_es3d(ctx, W, H, m, rx, ry) {
    var pl=m.data.planned||[0], ea=m.data.earned||[0];
    var cx=W/2,cy=H/2+10,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var n=pl.length, xSpan=130;
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:60-pl[i]/70*80,z:-20});
      var p2=t({x:x2,y:60-pl[i+1]/70*80,z:-20});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.stroke();
      ctx.setLineDash([]);
    }
    for(var i=0;i<ea.length-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:60-ea[i]/70*80,z:10});
      var p2=t({x:x2,y:60-ea[i+1]/70*80,z:10});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='#4ea0ff';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#4ea0ff';ctx.fill();
    }
    for(var i=1;i<ea.length;i++){
      var ey=ea[i];
      var esT=i;
      for(var j=0;j<n-1;j++){
        if(pl[j]<=ey&&pl[j+1]>=ey){esT=j+(ey-pl[j])/(pl[j+1]-pl[j]);break;}
      }
      var actualX=(i/(n-1)-0.5)*xSpan;
      var esX=(esT/(n-1)-0.5)*xSpan;
      var yPos=60-ey/70*80;
      var pt1=t({x:actualX,y:yPos,z:10}),pt2=t({x:esX,y:yPos,z:-20});
      if(!isFinite(pt1.x))continue;
      ctx.beginPath();ctx.moveTo(pt1.x,pt1.y);ctx.lineTo(pt2.x,pt2.y);
      ctx.strokeStyle='rgba(226,177,60,0.5)';ctx.lineWidth=1;ctx.stroke();
    }
    var ep=t({x:xSpan/2+5,y:60-ea[ea.length-1]/70*80,z:10});
    var pp=t({x:xSpan/2+5,y:60-pl[n-1]/70*80,z:-20});
    if(isFinite(ep.x)){
      ctx.font='9px SFMono-Regular,monospace';
      ctx.fillStyle='#4ea0ff';ctx.fillText('Earned',ep.x,ep.y);
      ctx.fillStyle='rgba(159,176,204,0.7)';ctx.fillText('Planned',pp.x,pp.y);
    }
  }

  /* ---------- 1.8 TCPI — 2D concentric gauge dials ---------- */
  function render_tcpi3d(ctx, W, H, m, rx, ry) {
    ctx.clearRect(0,0,W,H);
    var cx=W/2, cy=H/2+20;
    var d=m.data;
    var tcpiVal=(d.bac>0&&d.ac>0&&d.ev>0&&d.bac>d.ac)?(d.bac-d.ev)/(d.bac-d.ac):d.tcpi||1.0;
    var gauges=[
      {label:'Current CPI',  val:d.cpi||0.929, min:0.8, max:1.2, R:72, col:'#e2b13c', lw:10},
      {label:'Required TCPI',val:tcpiVal,       min:0.8, max:1.2, R:50, col:'#e0556b', lw:10}
    ];
    gauges.forEach(function(g){
      var startA=Math.PI*0.8, endA=Math.PI*2.2;
      var range=g.max-g.min;
      var v=Math.min(Math.max(g.val,g.min),g.max);
      var valA=startA+(v-g.min)/range*(endA-startA);
      ctx.beginPath();ctx.arc(cx,cy,g.R,startA,endA);
      ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=g.lw;ctx.stroke();
      ctx.beginPath();ctx.arc(cx,cy,g.R,startA,valA);
      ctx.strokeStyle=g.col;ctx.lineWidth=g.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';
      var okA=startA+(1.0-g.min)/range*(endA-startA);
      ctx.beginPath();ctx.arc(cx,cy,g.R,okA-0.02,okA+0.02);
      ctx.strokeStyle='#3fcaa6';ctx.lineWidth=g.lw+4;ctx.stroke();
      ctx.beginPath();ctx.arc(cx+g.R*Math.cos(valA),cy+g.R*Math.sin(valA),5,0,Math.PI*2);
      ctx.fillStyle=g.col;ctx.fill();
      ctx.font='bold 12px SFMono-Regular,monospace';ctx.fillStyle=g.col;
      ctx.textAlign='center';
      var lx=cx+(g.R+18)*Math.cos(valA), ly=cy+(g.R+18)*Math.sin(valA);
      ctx.fillText(g.val?g.val.toFixed(3):tcpiVal.toFixed(3),lx,ly);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
      ctx.fillText(g.label,cx,cy+(g.R===72?-82:-62));
      ctx.textAlign='left';
    });
    var gap=((tcpiVal-(d.cpi||0.929))*100).toFixed(1);
    ctx.textAlign='center';
    ctx.font='bold 11px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
    ctx.fillText('+'+(gap>0?gap:'0')+'% gap',cx,cy+8);
    ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
    ctx.fillText('TCPI vs CPI',cx,cy+22);
    ctx.textAlign='left';
  }

  /* ---------- 1.9 VAC — 3D concentric arc rings ---------- */
  function render_vac3d(ctx, W, H, m, rx, ry) {
    var d=m.data;
    var cx=W/2,cy=H/2+8;
    function t(pt){return {x:cx+pt.x, y:cy+pt.z, s:1};}  // flat 2D donut (rings read top-down, not tilted)
    ctx.clearRect(0,0,W,H);
    var eac=d.eac||(d.bac/0.929);
    var vac=d.bac-eac;
    var vacPct=Math.abs(vac)/d.bac;
    var rings=[
      {R:88,lw:14,col:'#e0556b',label:'Overrun',val:'+'+Math.abs(vacPct*100).toFixed(1)+'%',pct:vacPct*2,partial:true},
      {R:68,lw:14,col:'#4ea0ff',label:'BAC',val:'$'+(d.bac/1e6).toFixed(1)+'M',pct:1.0,partial:false},
      {R:48,lw:14,col:'#3fcaa6',label:'EV earned',val:d.ev>0?Math.round(d.ev/d.bac*100)+'%':'—',pct:d.ev>0?d.ev/d.bac:0.37,partial:true},
      {R:28,lw:14,col:'#e2b13c',label:'AC spent',val:d.ac>0?Math.round(d.ac/d.bac*100)+'%':'—',pct:d.ac>0?d.ac/d.bac:0.40,partial:true}
    ];
    var startA=-Math.PI/2;
    rings.forEach(function(ring){
      var steps=64;
      var bgPts=[];
      for(var i=0;i<=steps;i++){
        var a=startA+(i/steps)*Math.PI*2;
        bgPts.push(t({x:ring.R*Math.cos(a),y:0,z:ring.R*Math.sin(a)}));
      }
      ctx.beginPath();bgPts.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
      ctx.strokeStyle='rgba(38,52,79,0.55)';ctx.lineWidth=ring.lw;ctx.stroke();
      var arcEnd=ring.partial?Math.round(steps*Math.min(ring.pct,1)):steps;
      var arcPts=bgPts.slice(0,arcEnd+1);
      if(arcPts.length>1){
        ctx.beginPath();arcPts.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
        ctx.strokeStyle=ring.col;ctx.lineWidth=ring.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';
      }
      var tipA=startA+Math.min(ring.pct,1)*Math.PI*2*(ring.partial?1:0.25);
      var tipPt=t({x:ring.R*Math.cos(tipA),y:0,z:ring.R*Math.sin(tipA)});
      var callR=ring.R+28;
      var callPt=t({x:callR*Math.cos(tipA),y:-4,z:callR*Math.sin(tipA)});
      if(isFinite(tipPt.x)&&isFinite(callPt.x)){
        ctx.beginPath();ctx.moveTo(tipPt.x,tipPt.y);ctx.lineTo(callPt.x,callPt.y);
        ctx.strokeStyle=ring.col+'88';ctx.lineWidth=1;ctx.stroke();
        ctx.font='bold 9px SFMono-Regular,monospace';
        var tw=ctx.measureText(ring.label+' '+ring.val).width+10;
        var px=callPt.x-tw/2, py=callPt.y-8;
        if(ctx.roundRect)ctx.roundRect(px,py,tw,16,4); else ctx.rect(px,py,tw,16);
        ctx.fillStyle=ring.col+'22';ctx.fill();
        ctx.strokeStyle=ring.col+'66';ctx.lineWidth=0.8;ctx.stroke();
        ctx.fillStyle=ring.col;ctx.textAlign='center';
        ctx.fillText(ring.label+' '+ring.val,callPt.x,callPt.y+3);
        ctx.textAlign='left';
      }
    });
    ctx.textAlign='center';
    ctx.font='bold 10px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
    ctx.fillText('VAC '+(vac<0?'−':'+')+' $'+(Math.abs(vac)/1e6).toFixed(1)+'M',cx,cy+2);
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
    ctx.fillText('EAC $'+(eac/1e6).toFixed(1)+'M vs BAC $'+(d.bac/1e6).toFixed(1)+'M',cx,cy+14);
    ctx.textAlign='left';
  }

  /* ---------- 1.10 Budget Execution Rate — 3D dual area surfaces ---------- */
  function render_ber3d(ctx, W, H, m, rx, ry) {
    var d=m.data;
    var cx=W/2,cy=H/2+10,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var n=(d.periods||[]).length||6, xSpan=130, base=60;
    var planned=d.planned||[], actual=d.actual||[];
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-planned[i]*95, y2=base-planned[i+1]*95;
      var pts=[
        t({x:x1,y:y1,z:-20}),t({x:x2,y:y2,z:-20}),
        t({x:x2,y:base,z:-20}),t({x:x1,y:base,z:-20})
      ];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);
      pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle='rgba(159,176,204,0.12)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);
      ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1.5;ctx.setLineDash([3,3]);ctx.stroke();
      ctx.setLineDash([]);
    }
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan, x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-actual[i]*95, y2=base-actual[i+1]*95;
      var col2=actual[i]<planned[i]*0.95?'#e2b13c':'#4ea0ff';
      var pts=[
        t({x:x1,y:y1,z:15}),t({x:x2,y:y2,z:15}),
        t({x:x2,y:base,z:15}),t({x:x1,y:base,z:15})
      ];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);
      pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle=col2+'28';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);
      ctx.strokeStyle=col2;ctx.lineWidth=2;ctx.stroke();
      ctx.beginPath();ctx.arc(pts[0].x,pts[0].y,3,0,Math.PI*2);ctx.fillStyle=col2;ctx.fill();
    }
    for(var i=0;i<n;i++){
      var xpos=(i/(n-1)-0.5)*xSpan;
      var yP=base-(planned[i]||0)*95, yA=base-(actual[i]||0)*95;
      var pp=t({x:xpos,y:yP,z:-20}), pa=t({x:xpos,y:yA,z:15});
      if(!isFinite(pp.x))continue;
      ctx.beginPath();ctx.moveTo(pp.x,pp.y);ctx.lineTo(pa.x,pa.y);
      ctx.strokeStyle='rgba(226,177,60,0.25)';ctx.lineWidth=0.7;ctx.stroke();
      var lp=t({x:xpos,y:base+8,z:0});
      if(isFinite(lp.x)&&d.periods){
        ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
        ctx.textAlign='center';ctx.fillText(d.periods[i]||'',lp.x,lp.y);ctx.textAlign='left';
      }
    }
    ctx.font='9px SFMono-Regular,monospace';
    ctx.fillStyle='rgba(159,176,204,0.7)';ctx.fillText('── Planned',10,14);
    ctx.fillStyle='#4ea0ff';ctx.fillText('── Actual',10,26);
  }

  /* ---------- 1.11 Regression to Mean CPI — 3D line + convergence ---------- */
  function render_rtm3d(ctx, W, H, m, rx, ry) {
    var d=m.data;
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var nh=d.cpiHistory.length, nf=d.predicted.length;
    var total=nh+nf, xSpan=130;
    var allVals=d.cpiHistory.concat(d.predicted);
    var mean=allVals.reduce(function(a,b){return a+b;},0)/allVals.length;
    mean=Math.min(1.02,Math.max(0.90,mean));
    var ml1=t({x:-xSpan/2,y:50-(mean-0.88)/0.14*80,z:-20});
    var ml2=t({x:xSpan/2,y:50-(mean-0.88)/0.14*80,z:-20});
    if(isFinite(ml1.x)){
      ctx.beginPath();ctx.moveTo(ml1.x,ml1.y);ctx.lineTo(ml2.x,ml2.y);
      ctx.strokeStyle='rgba(63,202,166,0.4)';ctx.lineWidth=0.8;ctx.setLineDash([3,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';ctx.fillText('Long-run mean',ml1.x+4,ml1.y-3);
    }
    for(var i=0;i<nh-1;i++){
      var x1=(i/(total-1)-0.5)*xSpan, x2=((i+1)/(total-1)-0.5)*xSpan;
      var p1=t({x:x1,y:50-(d.cpiHistory[i]-0.88)/0.14*80,z:0});
      var p2=t({x:x2,y:50-(d.cpiHistory[i+1]-0.88)/0.14*80,z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='#e0556b';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#e0556b';ctx.fill();
    }
    var allPred=[d.cpiHistory[nh-1]].concat(d.predicted);
    for(var i=0;i<allPred.length-1;i++){
      var xi=(nh-1+i)/(total-1), xi2=(nh+i)/(total-1);
      var p1=t({x:(xi-0.5)*xSpan,y:50-(allPred[i]-0.88)/0.14*80,z:0});
      var p2=t({x:(xi2-0.5)*xSpan,y:50-(allPred[i+1]-0.88)/0.14*80,z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle='#4ea0ff';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.stroke();
      ctx.setLineDash([]);
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#4ea0ff';ctx.fill();
    }
  }

  /* ---------- 1.12 ICE Ratio — 3D arc rings ---------- */
  function render_ice3d(ctx, W, H, m, rx, ry) {
    var d=m.data;
    var cx=W/2,cy=H/2+8;
    function t(pt){return {x:cx+pt.x, y:cy+pt.z, s:1};}  // flat 2D donut (rings read top-down, not tilted)
    ctx.clearRect(0,0,W,H);
    var maxV=d.iceHigh*1.1;
    var rings2=[
      {R:80,lw:18,col:'#e0556b',label:'ICE range',val:'$'+(d.iceLow/1e6).toFixed(1)+'–'+(d.iceHigh/1e6).toFixed(1)+'M',
       startPct:(d.iceLow-d.bac)/(maxV-d.bac||1), endPct:(d.iceHigh-d.bac)/(maxV-d.bac||1), partial:true},
      {R:56,lw:14,col:'#e2b13c',label:'Contractor EAC',val:'$'+(d.contractorEac/1e6).toFixed(1)+'M',pct:1.0,partial:false},
      {R:32,lw:14,col:'#4ea0ff',label:'BAC',val:'$'+(d.bac/1e6).toFixed(1)+'M',pct:1.0,partial:false}
    ];
    var startA2=-Math.PI/2;
    rings2.forEach(function(ring){
      var steps=64;
      var bgPts=[];
      for(var i=0;i<=steps;i++){
        var a=startA2+(i/steps)*Math.PI*2;
        bgPts.push(t({x:ring.R*Math.cos(a),y:0,z:ring.R*Math.sin(a)}));
      }
      ctx.beginPath();bgPts.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
      ctx.strokeStyle='rgba(38,52,79,0.55)';ctx.lineWidth=ring.lw;ctx.stroke();
      var arcPts;
      if(ring.partial){
        var s=Math.round(steps*Math.max(0,ring.startPct)), e=Math.round(steps*Math.min(1,ring.endPct));
        arcPts=bgPts.slice(s,e+1);
      } else {
        arcPts=bgPts;
      }
      if(arcPts&&arcPts.length>1){
        ctx.beginPath();arcPts.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
        ctx.strokeStyle=ring.col;ctx.lineWidth=ring.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';
      }
      var midPct=ring.partial?(ring.startPct+ring.endPct)/2:0.62;
      var midA=startA2+midPct*Math.PI*2;
      var tipPt=t({x:ring.R*Math.cos(midA),y:0,z:ring.R*Math.sin(midA)});
      var callR=ring.R+30;
      var callPt=t({x:callR*Math.cos(midA),y:-4,z:callR*Math.sin(midA)});
      if(isFinite(tipPt.x)&&isFinite(callPt.x)){
        ctx.beginPath();ctx.moveTo(tipPt.x,tipPt.y);ctx.lineTo(callPt.x,callPt.y);
        ctx.strokeStyle=ring.col+'88';ctx.lineWidth=1;ctx.stroke();
        ctx.font='bold 9px SFMono-Regular,monospace';
        var tw=ctx.measureText(ring.label).width+10;
        var px=callPt.x-tw/2, py=callPt.y-16;
        if(ctx.roundRect)ctx.roundRect(px,py,tw,26,4); else ctx.rect(px,py,tw,26);
        ctx.fillStyle=ring.col+'22';ctx.fill();
        ctx.strokeStyle=ring.col+'66';ctx.lineWidth=0.8;ctx.stroke();
        ctx.fillStyle=ring.col;ctx.textAlign='center';
        ctx.fillText(ring.label,callPt.x,callPt.y-5);
        ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';
        ctx.fillText(ring.val,callPt.x,callPt.y+6);
        ctx.textAlign='left';
      }
    });
    var iceRatio=d.contractorEac>0?d.iceEac/d.contractorEac:1;
    var icePct=(d.iceEac-d.bac)/(maxV-d.bac||1);
    var iceA=startA2+icePct*Math.PI*2;
    var iceP=t({x:80*Math.cos(iceA),y:0,z:80*Math.sin(iceA)});
    if(isFinite(iceP.x)){
      ctx.beginPath();ctx.arc(iceP.x,iceP.y,5,0,Math.PI*2);
      ctx.fillStyle='#ffffff';ctx.fill();
      ctx.strokeStyle='#e0556b';ctx.lineWidth=2;ctx.stroke();
    }
    ctx.textAlign='center';
    ctx.font='bold 10px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
    ctx.fillText('ICE Ratio',cx,cy-4);
    ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle='#e2b13c';
    ctx.fillText(iceRatio.toFixed(3)+'  Gap +$'+((d.iceEac-d.contractorEac)/1e6).toFixed(1)+'M',cx,cy+10);
    ctx.textAlign='left';
  }

  /* ---------- canvas wiring helper (zoom + pan + rotate) ---------- */
  function wireChart3d(canvas, renderFn, moduleData, opts) {
    var options = opts || {};
    var isDraggable = options.draggable !== false;
    var dpr = window.devicePixelRatio || 1;
    var wrap = canvas.parentElement;
    function resize() {
      var w = (wrap && wrap.clientWidth) || 500;
      canvas.width = w * dpr;
      canvas.height = 190 * dpr;
      canvas.style.width = w + 'px';
      canvas.style.height = '190px';
    }
    resize();
    var ctx = canvas.getContext('2d');
    var rx = options.rx !== undefined ? options.rx : 0.28;
    var ry = options.ry !== undefined ? options.ry : -0.35;
    var zoom = 1, panX = 0, panY = 0;
    function redraw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.translate(panX, panY);
      ctx.scale(zoom, zoom);
      renderFn(ctx, (canvas.width / dpr) / zoom, (canvas.height / dpr) / zoom, moduleData, rx, ry);
      ctx.restore();
    }
    redraw();
    // Scroll = zoom (every canvas, including 2D-only)
    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      zoom = Math.max(0.3, Math.min(5, zoom * (e.deltaY > 0 ? 0.92 : 1.09)));
      redraw();
    }, { passive: false });
    if (isDraggable) {
      var dragging = false, lastX = 0, lastY = 0, mode = 'rotate';
      canvas.style.cursor = 'grab';
      canvas.addEventListener('mousedown', function(e) {
        dragging = true; lastX = e.clientX; lastY = e.clientY;
        mode = e.shiftKey ? 'pan' : 'rotate';
        canvas.style.cursor = mode === 'pan' ? 'move' : 'grabbing';
      });
      window.addEventListener('mouseup', function() {
        dragging = false; canvas.style.cursor = 'grab';
      });
      canvas.addEventListener('mousemove', function(e) {
        if (!dragging) return;
        var dx = e.clientX - lastX, dy = e.clientY - lastY;
        if (mode === 'pan') { panX += dx; panY += dy; }
        else { ry += dx * 0.005; rx += dy * 0.005; }
        lastX = e.clientX; lastY = e.clientY;
        redraw();
      });
    } else {
      // 2D-only canvases: shift+drag still pans
      var pdrag = false, plx = 0, ply = 0;
      canvas.addEventListener('mousedown', function(e) {
        if (!e.shiftKey) return;
        pdrag = true; plx = e.clientX; ply = e.clientY; canvas.style.cursor = 'move';
      });
      window.addEventListener('mouseup', function() { pdrag = false; canvas.style.cursor = ''; });
      canvas.addEventListener('mousemove', function(e) {
        if (!pdrag) return;
        panX += e.clientX - plx; panY += e.clientY - ply;
        plx = e.clientX; ply = e.clientY;
        redraw();
      });
    }
    window.addEventListener('resize', function() { resize(); redraw(); });
  }

  /* ---------- Cat 2 helper ---------- */
  function pillDraw(ctx, x, y, text, col) {
    ctx.font='bold 9px SFMono-Regular,monospace';
    var tw=ctx.measureText(text).width+10;
    if(ctx.roundRect)ctx.roundRect(x-tw/2,y-8,tw,16,4);else ctx.rect(x-tw/2,y-8,tw,16);
    ctx.fillStyle=col+'22';ctx.fill();ctx.strokeStyle=col+'66';ctx.lineWidth=0.8;ctx.stroke();
    ctx.fillStyle=col;ctx.textAlign='center';ctx.fillText(text,x,y+3);ctx.textAlign='left';
  }

  /* ---------- 2.1 PERT Network Criticality — 3D node graph ---------- */
  function render_pert3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var nodes=d.nodes||[
      {label:'Start',    x:-100,y:0,  z:0,  col:'#3fcaa6'},
      {label:'Design',   x:-55, y:-30,z:-15,col:'#4ea0ff'},
      {label:'Procure',  x:-55, y:25, z:18, col:'#4ea0ff'},
      {label:'Found',    x:0,   y:-40,z:-8, col:'#e2b13c'},
      {label:'Structure',x:0,   y:10, z:18, col:'#e2b13c'},
      {label:'MEP',      x:55,  y:-20,z:-20,col:'#e0556b'},
      {label:'Finish',   x:100, y:0,  z:0,  col:'#e0556b'}
    ];
    var edges=d.edges||[
      {f:0,to:1,c:false},{f:0,to:2,c:false},{f:1,to:3,c:true},
      {f:2,to:4,c:false},{f:3,to:5,c:true},{f:4,to:5,c:false},{f:5,to:6,c:true}
    ];
    var criticality=d.criticality||0.72;
    edges.forEach(function(e){
      var p1=t(nodes[e.f]),p2=t(nodes[e.to]);
      if(!isFinite(p1.x))return;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle=e.c?'#e0556b':'rgba(78,160,255,0.4)';ctx.lineWidth=e.c?2:1;ctx.stroke();
      if(e.c){
        var mx=(p1.x+p2.x)/2,my=(p1.y+p2.y)/2,ang=Math.atan2(p2.y-p1.y,p2.x-p1.x);
        ctx.save();ctx.translate(mx,my);ctx.rotate(ang);
        ctx.beginPath();ctx.moveTo(-4,-3);ctx.lineTo(4,0);ctx.lineTo(-4,3);
        ctx.fillStyle='#e0556b';ctx.fill();ctx.restore();
      }
    });
    nodes.forEach(function(n){
      var p=t(n);if(!isFinite(p.x))return;
      var r=Math.max(12,15*p.s);
      ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);
      ctx.fillStyle=n.col+'22';ctx.fill();ctx.strokeStyle=n.col;ctx.lineWidth=1.8;ctx.stroke();
      ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=n.col;
      ctx.textAlign='center';ctx.fillText(n.label,p.x,p.y+3);ctx.textAlign='left';
    });
    ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
    ctx.fillText('Critical path · Criticality '+criticality.toFixed(2),12,16);
  }

  /* ---------- 2.2 Line of Balance — 2D classic diagonal LOB ---------- */
  function render_lob2d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var buffer=d.buffer||2.1, threshold=d.threshold||3.0;
    var padL=40,padR=20,padT=20,padB=28;
    var cW=W-padL-padR, cH=H-padT-padB;
    var units=10, periods=12;
    ctx.clearRect(0,0,W,H);
    var crews=d.crews||[
      {name:'Foundation',col:'#4ea0ff',slope:1.00,start:0},
      {name:'Structure', col:'#3fcaa6',slope:0.92,start:18},
      {name:'MEP',       col:'#e2b13c',slope:0.85,start:38},
      {name:'Finishes',  col:'#e0556b',slope:0.78,start:62}
    ];
    // Grid
    for(var g=0;g<=4;g++){
      var gy=padT+g*(cH/4);
      ctx.beginPath();ctx.moveTo(padL,gy);ctx.lineTo(padL+cW,gy);
      ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.5;ctx.stroke();
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
      ctx.textAlign='right';ctx.fillText(String(units-g*(units/4)),padL-4,gy+4);ctx.textAlign='left';
    }
    // Min buffer threshold (green dashed)
    ctx.beginPath();ctx.moveTo(padL,padT+cH*0.55);ctx.lineTo(padL+cW,padT+cH*0.55);
    ctx.strokeStyle='rgba(63,202,166,0.5)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';
    ctx.fillText('Min buffer '+threshold.toFixed(1)+'d',padL+4,padT+cH*0.55-4);
    // Crew diagonal lines
    crews.forEach(function(crew){
      ctx.beginPath();
      for(var u=0;u<=units;u++){
        var ti=(crew.start+u/crew.slope)/100*periods;
        var x=padL+(ti/periods)*cW, y=padT+(1-u/units)*cH;
        u===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
      }
      ctx.strokeStyle=crew.col;ctx.lineWidth=2.5;ctx.stroke();
      // Label at top of line
      var tiEnd=(crew.start+units/crew.slope)/100*periods;
      var lx=padL+(tiEnd/periods)*cW, ly=padT;
      if(lx<padL+cW-4){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=crew.col;ctx.fillText(crew.name,lx+3,ly+12);}
    });
    // Amber bracket showing buffer gap
    var gapX=padL+cW*0.58, gapY1=padT+cH*0.30, gapY2=gapY1+buffer/units*cH;
    ctx.beginPath();
    ctx.moveTo(gapX-7,gapY1);ctx.lineTo(gapX,gapY1);ctx.lineTo(gapX,gapY2);ctx.lineTo(gapX-7,gapY2);
    ctx.strokeStyle='#e2b13c';ctx.lineWidth=1.5;ctx.stroke();
    ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle='#e2b13c';
    ctx.fillText('Buffer '+buffer.toFixed(1)+'d ⚠',gapX+4,(gapY1+gapY2)/2+3);
    // Axis labels
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='center';
    ctx.fillText('Time →',padL+cW/2,H-6);ctx.textAlign='left';
    ctx.save();ctx.translate(10,padT+cH/2);ctx.rotate(-Math.PI/2);
    ctx.textAlign='center';ctx.fillText('Units',0,0);ctx.restore();
  }

  /* ---------- 2.3 CCPM Buffer Health — 3D fever chart ---------- */
  function render_ccpm3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var zones=[
      {y1:0, y2:33,col:'#3fcaa6',label:'Green'},
      {y1:33,y2:66,col:'#e2b13c',label:'Amber'},
      {y1:66,y2:100,col:'#e0556b',label:'Red'}
    ];
    zones.forEach(function(z){
      var pts=[t({x:-55,y:50-z.y1,z:-25}),t({x:55,y:50-z.y1,z:-25}),
               t({x:55,y:50-z.y2,z:-25}),t({x:-55,y:50-z.y2,z:-25})];
      if(!pts.every(function(p){return isFinite(p.x);}))return;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle=z.col+'14';ctx.fill();ctx.strokeStyle=z.col+'30';ctx.lineWidth=0.5;ctx.stroke();
      var lp=t({x:-68,y:50-(z.y1+z.y2)/2,z:-25});
      if(isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=z.col+'aa';ctx.fillText(z.label,lp.x,lp.y+3);}
    });
    var chainPct=d.chainPct||52, bufPct=d.bufPct||38;
    var traj=d.traj||[{c:5,b:2},{c:12,b:8},{c:20,b:14},{c:28,b:22},{c:38,b:35},{c:chainPct,b:bufPct}];
    var tpts=traj.map(function(pt){return t({x:(pt.c/100-0.5)*110,y:50-pt.b,z:0});});
    ctx.beginPath();tpts.forEach(function(p,i){if(!isFinite(p.x))return;i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
    ctx.strokeStyle='#e2b13c';ctx.lineWidth=2.5;ctx.stroke();
    tpts.forEach(function(p){if(!isFinite(p.x))return;ctx.beginPath();ctx.arc(p.x,p.y,3,0,Math.PI*2);ctx.fillStyle='#e2b13c';ctx.fill();});
    var cur=tpts[tpts.length-1];
    if(isFinite(cur.x)){
      ctx.beginPath();ctx.arc(cur.x,cur.y,7,0,Math.PI*2);ctx.strokeStyle='#e2b13c';ctx.lineWidth=2;ctx.stroke();
      pillDraw(ctx,cur.x+26,cur.y,'Now '+chainPct+'%/'+bufPct+'%','#e2b13c');
    }
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('X: Chain %   Y: Buffer %',12,H-12);
  }

  /* ---------- 2.4 Schedule Compression Index — 3D line + forecast ---------- */
  function render_sci3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var hist=d.history||[1.00,1.00,0.99,0.98,0.97,0.95,0.94,0.94];
    var fore=d.forecast||[0.94,0.93,0.92];
    var xSpan=120,n=hist.length,total=n+fore.length;
    function yv(v){return 50-(v-0.88)/0.16*90;}
    var bp1=t({x:-xSpan/2,y:yv(1.0),z:-20}),bp2=t({x:xSpan/2,y:yv(1.0),z:-20});
    if(isFinite(bp1.x)){
      ctx.beginPath();ctx.moveTo(bp1.x,bp1.y);ctx.lineTo(bp2.x,bp2.y);
      ctx.strokeStyle='rgba(63,202,166,0.5)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';ctx.fillText('Baseline 1.0',bp1.x,bp1.y-4);
    }
    for(var i=0;i<n-1;i++){
      var x1=(i/(total-1)-0.5)*xSpan,x2=((i+1)/(total-1)-0.5)*xSpan;
      var p1=t({x:x1,y:yv(hist[i]),z:0}),p2=t({x:x2,y:yv(hist[i+1]),z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#f0c040';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#f0c040';ctx.fill();
    }
    var allF=[hist[n-1]].concat(fore);
    for(var i2=0;i2<allF.length-1;i2++){
      var xi=(n-1+i2)/(total-1),xi2=(n+i2)/(total-1);
      var p1b=t({x:(xi-0.5)*xSpan,y:yv(allF[i2]),z:0}),p2b=t({x:(xi2-0.5)*xSpan,y:yv(allF[i2+1]),z:0});
      if(!isFinite(p1b.x))continue;
      ctx.beginPath();ctx.moveTo(p1b.x,p1b.y);ctx.lineTo(p2b.x,p2b.y);
      ctx.strokeStyle='#f0c040';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    }
    var lp=t({x:((n-1)/(total-1)-0.5)*xSpan,y:yv(hist[n-1]),z:0});
    if(isFinite(lp.x)) pillDraw(ctx,lp.x,lp.y-16,'SCI '+hist[n-1].toFixed(2),'#f0c040');
  }

  /* ---------- 2.5 Float Consumption — 3D area surface ---------- */
  function render_float3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var fh=d.history||[42,38,34,29,24,18];
    var threshold=d.threshold||15;
    var n=fh.length, maxF=Math.max.apply(null,fh)||42, xSpan=120;
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=55-fh[i]/maxF*90,y2=55-fh[i+1]/maxF*90;
      var col=fh[i]>threshold*2?'#4ea0ff':fh[i]>threshold?'#e2b13c':'#e0556b';
      var pts=[t({x:x1,y:y1,z:12}),t({x:x2,y:y2,z:12}),t({x:x2,y:55,z:12}),t({x:x1,y:55,z:12})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle=col+'28';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);
      ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(pts[0].x,pts[0].y,3,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
    }
    var tp1=t({x:-xSpan/2,y:55-threshold/maxF*90,z:-15}),tp2=t({x:xSpan/2,y:55-threshold/maxF*90,z:-15});
    if(isFinite(tp1.x)){
      ctx.beginPath();ctx.moveTo(tp1.x,tp1.y);ctx.lineTo(tp2.x,tp2.y);
      ctx.strokeStyle='#e0556b88';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';
      ctx.fillText('Critical '+threshold+'d',tp1.x+4,tp1.y-4);
    }
    var last=fh[n-1];
    var lp=t({x:xSpan*0.2,y:55-last/maxF*90,z:12});
    if(isFinite(lp.x)) pillDraw(ctx,lp.x,lp.y-14,last+'d remaining',last>threshold?'#e2b13c':'#e0556b');
  }

  /* ---------- 2.6 S-Curve Deviation — 3D dual surfaces ---------- */
  function render_scurve3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var pl=d.planned||[0,3,7,14,22,30,37,43,50,57,64,70];
    var ea=d.earned||[0,2,6,12,19,26,32,37,42,0,0,0];
    var n=pl.length, xSpan=120;
    var maxV=Math.max.apply(null,pl)||70;
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=55-pl[i]/maxV*90,y2=55-pl[i+1]/maxV*90;
      var pts=[t({x:x1,y:y1,z:-18}),t({x:x2,y:y2,z:-18}),t({x:x2,y:55,z:-18}),t({x:x1,y:55,z:-18})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle='rgba(159,176,204,0.08)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);
      ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1.5;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    }
    var eN=ea.filter(function(v){return v>0;}).length;
    for(var j=0;j<eN-1;j++){
      var ex1=(j/(n-1)-0.5)*xSpan,ex2=((j+1)/(n-1)-0.5)*xSpan;
      var ey1=55-ea[j]/maxV*90,ey2=55-ea[j+1]/maxV*90;
      var epts=[t({x:ex1,y:ey1,z:12}),t({x:ex2,y:ey2,z:12}),t({x:ex2,y:55,z:12}),t({x:ex1,y:55,z:12})];
      if(!epts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(epts[0].x,epts[0].y);epts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle='rgba(78,160,255,0.15)';ctx.fill();
      ctx.beginPath();ctx.moveTo(epts[0].x,epts[0].y);ctx.lineTo(epts[1].x,epts[1].y);
      ctx.strokeStyle='#4ea0ff';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(epts[1].x,epts[1].y,3,0,Math.PI*2);ctx.fillStyle='#4ea0ff';ctx.fill();
    }
    var ci2=eN-1;
    if(ci2>=0&&ci2<n){
      var pp=t({x:(ci2/(n-1)-0.5)*xSpan,y:55-pl[ci2]/maxV*90,z:-18});
      var ep=t({x:(ci2/(n-1)-0.5)*xSpan,y:55-ea[ci2]/maxV*90,z:12});
      if(isFinite(pp.x)&&isFinite(ep.x)){
        ctx.beginPath();ctx.moveTo(pp.x,pp.y);ctx.lineTo(ep.x,ep.y);
        ctx.strokeStyle='#e2b13c';ctx.lineWidth=2;ctx.stroke();
        var gap=Math.round((ea[ci2]-pl[ci2])/maxV*100);
        pillDraw(ctx,(pp.x+ep.x)/2+24,(pp.y+ep.y)/2,'Gap '+(gap>=0?'+':'')+gap+'%','#e2b13c');
      }
    }
  }

  /* ---------- 2.7 Milestone Trend Analysis — 3D MTA fan ---------- */
  function render_mta3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var ms=d.milestones||[
      {name:'Foundation',col:'#4ea0ff',fc:[10,10,11,12,13,13]},
      {name:'Structure', col:'#e2b13c',fc:[22,22,23,25,26,27]},
      {name:'MEP',       col:'#e0556b',fc:[36,36,37,39,41,43]},
      {name:'Handover',  col:'#9b6dff',fc:[48,49,50,52,55,58]}
    ];
    var periods=d.periods||6, xSpan=110;
    for(var p2=0;p2<periods;p2++){
      var x=(p2/(periods-1)-0.5)*xSpan;
      var ga=t({x:x,y:55,z:-25}),gb=t({x:x,y:-55,z:-25});
      if(!isFinite(ga.x))return;
      ctx.beginPath();ctx.moveTo(ga.x,ga.y);ctx.lineTo(gb.x,gb.y);
      ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();
    }
    var il1=t({x:-xSpan/2,y:55,z:-20}),il2=t({x:xSpan/2,y:-55,z:-20});
    if(isFinite(il1.x)){
      ctx.beginPath();ctx.moveTo(il1.x,il1.y);ctx.lineTo(il2.x,il2.y);
      ctx.strokeStyle='rgba(63,202,166,0.3)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    }
    ms.forEach(function(mi,mii){
      var pts=mi.fc.map(function(f,pi){return t({x:(pi/(periods-1)-0.5)*xSpan,y:50-(f/60)*100,z:mii*15-22});});
      ctx.beginPath();pts.forEach(function(p,i){if(!isFinite(p.x))return;i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
      ctx.strokeStyle=mi.col;ctx.lineWidth=2;ctx.stroke();
      pts.forEach(function(p,i){if(!isFinite(p.x))return;ctx.beginPath();ctx.arc(p.x,p.y,i===periods-1?5:3,0,Math.PI*2);ctx.fillStyle=mi.col;ctx.fill();});
      var lp=pts[pts.length-1];if(lp&&isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=mi.col;ctx.fillText(mi.name,lp.x+7,lp.y+3);}
    });
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('Upward slope = milestone slipping',12,H-12);
  }

  /* ---------- 2.8 Look-Ahead Schedule Health — 3D arc rings ---------- */
  function render_lookahead3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+8,fov=Math.min(W,H)*0.9;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    t = function(p){return {x:cx+p.x, y:cy+p.z, s:1};};  // flat 2D donut (rings read top-down, not tilted)
    var total=d.total||10, onTrack=d.onTrack||6, constrained=d.constrained||4;
    var rings=[
      {R:72,lw:16,col:'#3fcaa6',label:'Total planned',  val:total+' activities',  pct:1.0},
      {R:50,lw:16,col:'#4ea0ff',label:'On track',       val:onTrack+' activities',pct:onTrack/total},
      {R:28,lw:16,col:'#e0556b',label:'Constrained',    val:constrained+' act.',  pct:constrained/total}
    ];
    var startA=-Math.PI/2;
    rings.forEach(function(ring){
      var steps=64,bgPts=[];
      for(var i=0;i<=steps;i++){var a=startA+(i/steps)*Math.PI*2;bgPts.push(t({x:ring.R*Math.cos(a),y:0,z:ring.R*Math.sin(a)}));}
      ctx.beginPath();bgPts.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
      ctx.strokeStyle='rgba(38,52,79,0.55)';ctx.lineWidth=ring.lw;ctx.stroke();
      var arcPts=bgPts.slice(0,Math.round(steps*ring.pct)+1);
      if(arcPts.length>1){ctx.beginPath();arcPts.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});ctx.strokeStyle=ring.col;ctx.lineWidth=ring.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';}
      var tipA=startA+ring.pct*Math.PI;
      var tip=t({x:ring.R*Math.cos(tipA),y:0,z:ring.R*Math.sin(tipA)});
      var cp2=t({x:(ring.R+30)*Math.cos(tipA),y:-4,z:(ring.R+30)*Math.sin(tipA)});
      if(isFinite(tip.x)&&isFinite(cp2.x)){
        ctx.beginPath();ctx.moveTo(tip.x,tip.y);ctx.lineTo(cp2.x,cp2.y);ctx.strokeStyle=ring.col+'88';ctx.lineWidth=1;ctx.stroke();
        ctx.font='bold 9px SFMono-Regular,monospace';var tw=ctx.measureText(ring.label).width+10;
        if(ctx.roundRect)ctx.roundRect(cp2.x-tw/2,cp2.y-16,tw,26,4);else ctx.rect(cp2.x-tw/2,cp2.y-16,tw,26);
        ctx.fillStyle=ring.col+'22';ctx.fill();ctx.strokeStyle=ring.col+'66';ctx.lineWidth=0.8;ctx.stroke();
        ctx.fillStyle=ring.col;ctx.textAlign='center';ctx.fillText(ring.label,cp2.x,cp2.y-5);
        ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.fillText(ring.val,cp2.x,cp2.y+6);ctx.textAlign='left';
      }
    });
    ctx.textAlign='center';
    ctx.font='bold 10px SFMono-Regular,monospace';ctx.fillStyle='#e2b13c';
    ctx.fillText(Math.round(constrained/total*100)+'% constrained',cx,cy+2);
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('6-week look-ahead',cx,cy+14);ctx.textAlign='left';
  }

  /* ---------- 2.9 Resource Loading — 3D dual area surfaces ---------- */
  function render_resource3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var periods=d.periods||['M1','M2','M3','M4','M5','M6'];
    var pl=d.planned||[600,720,780,800,740,660];
    var act=d.actual||[580,690,740,760,710,0];
    var n=periods.length, xSpan=120, maxV=Math.max.apply(null,pl)||820;
    for(var i=0;i<n-1;i++){
      if(!pl[i+1])continue;
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=55-pl[i]/maxV*90,y2=55-pl[i+1]/maxV*90;
      var pts=[t({x:x1,y:y1,z:-18}),t({x:x2,y:y2,z:-18}),t({x:x2,y:55,z:-18}),t({x:x1,y:55,z:-18})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle='rgba(159,176,204,0.1)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);
      ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1.5;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    }
    var aN=act.filter(function(v){return v>0;}).length;
    for(var j=0;j<aN-1;j++){
      var ax1=(j/(n-1)-0.5)*xSpan,ax2=((j+1)/(n-1)-0.5)*xSpan;
      var ay1=55-act[j]/maxV*90,ay2=55-act[j+1]/maxV*90;
      var col=act[j]>=pl[j]*0.95?'#3fcaa6':'#f0c040';
      var apts=[t({x:ax1,y:ay1,z:12}),t({x:ax2,y:ay2,z:12}),t({x:ax2,y:55,z:12}),t({x:ax1,y:55,z:12})];
      if(!apts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(apts[0].x,apts[0].y);apts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();
      ctx.fillStyle=col+'25';ctx.fill();
      ctx.beginPath();ctx.moveTo(apts[0].x,apts[0].y);ctx.lineTo(apts[1].x,apts[1].y);
      ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(apts[1].x,apts[1].y,3,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
      var lp=t({x:ax1,y:60,z:0});
      if(isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='center';ctx.fillText(periods[j],lp.x,lp.y);ctx.textAlign='left';}
    }
    if(aN>0){
      var rli=(act.slice(0,aN).reduce(function(a,b){return a+b;},0)/pl.slice(0,aN).reduce(function(a,b){return a+b;},1));
      var rp=t({x:((aN-1)/(n-1)-0.5)*xSpan,y:55-act[aN-1]/maxV*90,z:12});
      if(isFinite(rp.x)) pillDraw(ctx,rp.x+22,rp.y-10,'RLI '+rli.toFixed(2),'#f0c040');
    }
  }

  /* ---------- 2.10 Schedule Risk P80 — 3D histogram ---------- */
  function render_schedp80(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var mean=d.mean||12, std=d.std||6;
    var p50val=d.p50||mean-std*0.42, p80val=d.p80||mean+std*0.84;
    var bars=36, minV=mean-std*2.5, maxV=mean+std*2.5, bw=3.8, depth=14;
    function gauss(x){return Math.exp(-0.5*Math.pow((x-mean)/std,2));}
    var heights=[];
    for(var i=0;i<bars;i++){heights.push(gauss(minV+(i+0.5)*(maxV-minV)/bars));}
    var maxH=Math.max.apply(null,heights)||1;
    heights.forEach(function(h,bi){
      /* jshint ignore:start */
      (function(idx){
        var xval=minV+(idx+0.5)*(maxV-minV)/bars;
        var xpos=(idx/bars-0.5)*bw*bars;
        var bh=h/maxH*90,yT=55-bh,yB=55;
        var col=xval>=p80val?'#e0556b':xval>=p50val?'#e2b13c':'#4ea0ff';
        function c3(dx,dy,dz){return t({x:xpos+dx,y:dy,z:dz});}
        var pts=[c3(-bw/2,yT,-depth/2),c3(bw/2,yT,-depth/2),c3(bw/2,yT,depth/2),c3(-bw/2,yT,depth/2),
                 c3(-bw/2,yB,-depth/2),c3(bw/2,yB,-depth/2),c3(bw/2,yB,depth/2),c3(-bw/2,yB,depth/2)];
        if(!pts.every(function(p){return isFinite(p.x);}))return;
        function face(idxArr,alpha){ctx.beginPath();ctx.moveTo(pts[idxArr[0]].x,pts[idxArr[0]].y);idxArr.forEach(function(j){ctx.lineTo(pts[j].x,pts[j].y);});ctx.closePath();ctx.fillStyle=col;ctx.globalAlpha=alpha;ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.3;ctx.stroke();ctx.globalAlpha=1;}
        face([0,1,2,3],0.88);face([4,5,1,0],0.65);face([5,6,2,1],0.45);
      })(bi);
      /* jshint ignore:end */
    });
    [{label:'P50 +'+(p50val>=0?p50val.toFixed(1):'0')+'d',val:p50val,col:'#3fcaa6'},
     {label:'P80 +'+(p80val>=0?p80val.toFixed(1):'0')+'d',val:p80val,col:'#e0556b'}].forEach(function(mk){
      var xp=((mk.val-minV)/(maxV-minV)*bars-0.5)*bw;
      var pl1=t({x:xp,y:-40,z:-depth/2}),pl2=t({x:xp,y:55,z:-depth/2});
      if(!isFinite(pl1.x))return;
      ctx.beginPath();ctx.moveTo(pl1.x,pl1.y);ctx.lineTo(pl2.x,pl2.y);ctx.strokeStyle=mk.col;ctx.lineWidth=1.5;ctx.stroke();
      pillDraw(ctx,pl1.x,pl1.y-6,mk.label,mk.col);
    });
  }

  /* ---------- 2.11 Critical Path Index — 3D line + near-critical ---------- */
  function render_cpisched3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var hist=d.history||[1.00,0.99,0.97,0.95,0.93,0.91,0.88,0.88];
    var fore=d.forecast||[0.87,0.86,0.85];
    var xSpan=120,n=hist.length,total=n+fore.length;
    function yv(v){return 50-(v-0.82)/0.22*90;}
    var bp1=t({x:-xSpan/2,y:yv(1.0),z:-20}),bp2=t({x:xSpan/2,y:yv(1.0),z:-20});
    if(isFinite(bp1.x)){
      ctx.beginPath();ctx.moveTo(bp1.x,bp1.y);ctx.lineTo(bp2.x,bp2.y);
      ctx.strokeStyle='rgba(63,202,166,0.5)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    }
    [{offset:0.025,col:'#4ea0ff88'},{offset:0.048,col:'#4ea0ff44'}].forEach(function(nc){
      for(var i=0;i<n-1;i++){
        var x1=(i/(total-1)-0.5)*xSpan,x2=((i+1)/(total-1)-0.5)*xSpan;
        var p1=t({x:x1,y:yv(hist[i]-nc.offset),z:-12}),p2=t({x:x2,y:yv(hist[i+1]-nc.offset),z:-12});
        if(!isFinite(p1.x))continue;
        ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle=nc.col;ctx.lineWidth=1;ctx.stroke();
      }
    });
    for(var i=0;i<n-1;i++){
      var x1=(i/(total-1)-0.5)*xSpan,x2=((i+1)/(total-1)-0.5)*xSpan;
      var p1=t({x:x1,y:yv(hist[i]),z:0}),p2=t({x:x2,y:yv(hist[i+1]),z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e2b13c';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#e2b13c';ctx.fill();
    }
    var allF=[hist[n-1]].concat(fore);
    for(var i2=0;i2<allF.length-1;i2++){
      var xi=(n-1+i2)/(total-1),xi2=(n+i2)/(total-1);
      var p1b=t({x:(xi-0.5)*xSpan,y:yv(allF[i2]),z:0}),p2b=t({x:(xi2-0.5)*xSpan,y:yv(allF[i2+1]),z:0});
      if(!isFinite(p1b.x))continue;
      ctx.beginPath();ctx.moveTo(p1b.x,p1b.y);ctx.lineTo(p2b.x,p2b.y);ctx.strokeStyle='#e2b13c';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    }
    var lp=t({x:((n-1)/(total-1)-0.5)*xSpan,y:yv(hist[n-1]),z:0});
    if(isFinite(lp.x)) pillDraw(ctx,lp.x,lp.y-16,'CPI '+hist[n-1].toFixed(2),'#e2b13c');
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#4ea0ff66';ctx.fillText('Near-critical paths in blue',12,H-12);
  }

  /* ---------- Cat 3 helper ---------- */
  function gauss3(x, mu, sig) { return Math.exp(-0.5 * Math.pow((x - mu) / sig, 2)); }

  /* ---------- 3.1 Reference Class Forecast — 3D histogram ---------- */
  function render_rcf3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var bac=d.bac||24900000,rcfP80=d.rcfP80||28400000;
    var mean=rcfP80*0.94,sig=1800000,bars=32,minV=bac*0.9,maxV=rcfP80*1.1,bw=4.2,depth=14;
    var heights=[];
    for(var i=0;i<bars;i++){heights.push(gauss3(minV+(i+0.5)*(maxV-minV)/bars,mean,sig));}
    var maxH=Math.max.apply(null,heights)||1;
    heights.forEach(function(h,bi){
      (function(idx){
        var xval=minV+(idx+0.5)*(maxV-minV)/bars;
        var xpos=(idx/bars-0.5)*bw*bars;
        var col=xval>bac?'#e0556b':'#4ea0ff';
        var bh=h/maxH*85,yT=55-bh,yB=55;
        function c3(dx,dy,dz){return t({x:xpos+dx,y:dy,z:dz});}
        var pts=[c3(-bw/2,yT,-depth/2),c3(bw/2,yT,-depth/2),c3(bw/2,yT,depth/2),c3(-bw/2,yT,depth/2),
                 c3(-bw/2,yB,-depth/2),c3(bw/2,yB,-depth/2),c3(bw/2,yB,depth/2),c3(-bw/2,yB,depth/2)];
        if(!pts.every(function(p){return isFinite(p.x);}))return;
        function face(idxA,alpha){ctx.beginPath();ctx.moveTo(pts[idxA[0]].x,pts[idxA[0]].y);idxA.forEach(function(j){ctx.lineTo(pts[j].x,pts[j].y);});ctx.closePath();ctx.fillStyle=col;ctx.globalAlpha=alpha;ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.3;ctx.stroke();ctx.globalAlpha=1;}
        face([0,1,2,3],0.88);face([4,5,1,0],0.65);face([5,6,2,1],0.45);
      })(bi);
    });
    var bacIdx=Math.round((bac-minV)/(maxV-minV)*bars);
    var bacX=(bacIdx/bars-0.5)*bw*bars;
    var bl1=t({x:bacX,y:-40,z:-depth/2}),bl2=t({x:bacX,y:55,z:-depth/2});
    if(isFinite(bl1.x)){ctx.beginPath();ctx.moveTo(bl1.x,bl1.y);ctx.lineTo(bl2.x,bl2.y);ctx.strokeStyle='#4ea0ff';ctx.lineWidth=1.5;ctx.stroke();pillDraw(ctx,bl1.x,bl1.y-6,'BAC $'+(bac/1e6).toFixed(1)+'M','#4ea0ff');}
    var p80Idx=Math.round((rcfP80-minV)/(maxV-minV)*bars);
    var p80X=(p80Idx/bars-0.5)*bw*bars;
    var pl1=t({x:p80X,y:-40,z:-depth/2}),pl2=t({x:p80X,y:55,z:-depth/2});
    if(isFinite(pl1.x)){ctx.beginPath();ctx.moveTo(pl1.x,pl1.y);ctx.lineTo(pl2.x,pl2.y);ctx.strokeStyle='#e0556b';ctx.lineWidth=1.5;ctx.stroke();pillDraw(ctx,pl1.x,pl1.y-22,'RCF P80 $'+(rcfP80/1e6).toFixed(1)+'M','#e0556b');}
  }

  /* ---------- 3.2 DSM Rework Propagation — 3D heat matrix (2D, no drag) ---------- */
  function render_dsm3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var disciplines=d.disciplines||['Arch','Struct','MEP','Civil','Interior'];
    var n=disciplines.length;
    var rework=d.rework||[[0,0.8,0.6,0.3,0.4],[0.2,0,0.9,0.5,0.3],[0.1,0.3,0,0.7,0.8],[0.1,0.2,0.4,0,0.5],[0.2,0.1,0.5,0.3,0]];
    var multiplier=d.multiplier||2.8;
    var cellSize=28,depth=12;
    var offsetX=-(n*cellSize)/2+cellSize/2;
    var offsetZ=-(n*cellSize)/2+cellSize/2;
    for(var row=0;row<n;row++){
      for(var col2=0;col2<n;col2++){
        if(row===col2)continue;
        var v=rework[row][col2];
        var xpos=offsetX+col2*cellSize;
        var zpos=offsetZ+row*cellSize;
        var bh=v*60,yT=40-bh,yB=40;
        var col=v>0.7?'#e0556b':v>0.4?'#e2b13c':'#4ea0ff';
        var pts=[t({x:xpos-cellSize/2+2,y:yT,z:zpos-depth/2}),t({x:xpos+cellSize/2-2,y:yT,z:zpos-depth/2}),t({x:xpos+cellSize/2-2,y:yT,z:zpos+depth/2}),t({x:xpos-cellSize/2+2,y:yT,z:zpos+depth/2}),
                 t({x:xpos-cellSize/2+2,y:yB,z:zpos-depth/2}),t({x:xpos+cellSize/2-2,y:yB,z:zpos-depth/2}),t({x:xpos+cellSize/2-2,y:yB,z:zpos+depth/2}),t({x:xpos-cellSize/2+2,y:yB,z:zpos+depth/2})];
        if(!pts.every(function(p){return isFinite(p.x);}))continue;
        (function(colr,ps){
          function face2(idx,alpha){ctx.beginPath();ctx.moveTo(ps[idx[0]].x,ps[idx[0]].y);idx.forEach(function(j){ctx.lineTo(ps[j].x,ps[j].y);});ctx.closePath();ctx.fillStyle=colr;ctx.globalAlpha=alpha;ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.3;ctx.stroke();ctx.globalAlpha=1;}
          face2([0,1,2,3],0.88);face2([4,5,1,0],0.65);face2([5,6,2,1],0.45);
        })(col,pts);
      }
    }
    for(var i=0;i<n;i++){
      var xlp=t({x:offsetX+i*cellSize,y:48,z:offsetZ-cellSize});
      var zlp=t({x:offsetX-cellSize,y:48,z:offsetZ+i*cellSize});
      if(isFinite(xlp.x)){ctx.font='7px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='center';ctx.fillText(disciplines[i],xlp.x,xlp.y);}
      if(isFinite(zlp.x)){ctx.textAlign='right';ctx.fillText(disciplines[i],zlp.x,zlp.y);ctx.textAlign='left';}
    }
    pillDraw(ctx,W/2,16,'Multiplier '+multiplier+'x','#e0556b');
  }

  /* ---------- 3.3 Contingency Burn Rate — 3D area + threshold ---------- */
  function render_contingency3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var total=d.total||1800000;
    var history=d.history||[0,180000,420000,720000,1080000,1224000];
    var n=history.length,xSpan=120,base=55;
    var pcts=history.map(function(v){return v/total;});
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-pcts[i]*90,y2=base-pcts[i+1]*90;
      var col=pcts[i+1]>0.75?'#e0556b':pcts[i+1]>0.50?'#e2b13c':'#4ea0ff';
      var pts=[t({x:x1,y:y1,z:12}),t({x:x2,y:y2,z:12}),t({x:x2,y:base,z:12}),t({x:x1,y:base,z:12})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle=col+'30';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(pts[1].x,pts[1].y,3,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
    }
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var r1=base-pcts[i]*90,r2=base-pcts[i+1]*90;
      var pts=[t({x:x1,y:base-90,z:-15}),t({x:x2,y:base-90,z:-15}),t({x:x2,y:r2,z:-15}),t({x:x1,y:r1,z:-15})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(63,202,166,0.08)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle='rgba(63,202,166,0.4)';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    }
    var tp1=t({x:-xSpan/2,y:base-0.80*90,z:-20}),tp2=t({x:xSpan/2,y:base-0.80*90,z:-20});
    if(isFinite(tp1.x)){ctx.beginPath();ctx.moveTo(tp1.x,tp1.y);ctx.lineTo(tp2.x,tp2.y);ctx.strokeStyle='#e0556b88';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('80% threshold',tp1.x+4,tp1.y-4);}
    var burned=Math.round(pcts[n-1]*100);
    var lp=t({x:xSpan/4,y:base-pcts[n-1]*90,z:12});
    if(isFinite(lp.x)) pillDraw(ctx,lp.x,lp.y-14,burned+'% burned',burned>75?'#e0556b':burned>50?'#e2b13c':'#4ea0ff');
  }

  /* ---------- 3.4 Labor Productivity Index — 3D line + band + forecast ---------- */
  function render_labor3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var history=d.history||[1.02,0.99,0.97,0.94,0.92,0.90,0.88];
    var fore=d.forecast||[0.88,0.87,0.86];
    var lpi=d.lpi||(history[history.length-1]);
    var xSpan=120,n=history.length,total=n+fore.length;
    function yv(v){return 50-(v-0.82)/0.26*90;}
    for(var i=0;i<n-1;i++){
      var x1=(i/(total-1)-0.5)*xSpan,x2=((i+1)/(total-1)-0.5)*xSpan;
      var y1=yv(history[i]),y2=yv(history[i+1]),band=4;
      var pts=[t({x:x1,y:y1-band,z:0}),t({x:x2,y:y2-band,z:0}),t({x:x2,y:y2+band,z:0}),t({x:x1,y:y1+band,z:0})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(226,177,60,0.1)';ctx.fill();
    }
    var bp1=t({x:-xSpan/2,y:yv(1.0),z:-20}),bp2=t({x:xSpan/2,y:yv(1.0),z:-20});
    if(isFinite(bp1.x)){ctx.beginPath();ctx.moveTo(bp1.x,bp1.y);ctx.lineTo(bp2.x,bp2.y);ctx.strokeStyle='rgba(63,202,166,0.4)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';ctx.fillText('Baseline 1.0',bp1.x,bp1.y-4);}
    for(var i=0;i<n-1;i++){
      var x1=(i/(total-1)-0.5)*xSpan,x2=((i+1)/(total-1)-0.5)*xSpan;
      var p1=t({x:x1,y:yv(history[i]),z:0}),p2=t({x:x2,y:yv(history[i+1]),z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e2b13c';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#e2b13c';ctx.fill();
    }
    var allF=[history[n-1]].concat(fore);
    for(var i=0;i<allF.length-1;i++){
      var xi=(n-1+i)/(total-1),xi2=(n+i)/(total-1);
      var p1=t({x:(xi-0.5)*xSpan,y:yv(allF[i]),z:0}),p2=t({x:(xi2-0.5)*xSpan,y:yv(allF[i+1]),z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e2b13c';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    }
    var lp=t({x:((n-1)/(total-1)-0.5)*xSpan,y:yv(history[n-1]),z:0});
    if(isFinite(lp.x)) pillDraw(ctx,lp.x,lp.y-16,'LPI '+lpi.toFixed(2),'#e2b13c');
  }

  /* ---------- 3.5 Material Cost Variance — 3D paired bars by trade ---------- */
  function render_material3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var trades=d.trades||[
      {name:'Structural',planned:1200000,actual:1380000,col:'#e0556b',x:-75},
      {name:'MEP',       planned:2100000,actual:2310000,col:'#e2b13c',x:-25},
      {name:'Finishes',  planned:800000, actual:820000, col:'#f0c040',x:25},
      {name:'Civil',     planned:600000, actual:588000, col:'#3fcaa6',x:75}
    ];
    var maxV=d.maxV||2500000,bw=26,depth=16,base=55;
    trades.forEach(function(tr){
      var ph=tr.planned/maxV*85,pyT=base-ph;
      var ppts=[t({x:tr.x-bw/2,y:pyT,z:-depth}),t({x:tr.x+bw/2,y:pyT,z:-depth}),t({x:tr.x+bw/2,y:pyT,z:0}),t({x:tr.x-bw/2,y:pyT,z:0}),
                t({x:tr.x-bw/2,y:base, z:-depth}),t({x:tr.x+bw/2,y:base, z:-depth}),t({x:tr.x+bw/2,y:base, z:0}),t({x:tr.x-bw/2,y:base, z:0})];
      if(!ppts.every(function(p){return isFinite(p.x);}))return;
      (function(ps){
        function faceP(idx,alpha){ctx.beginPath();ctx.moveTo(ps[idx[0]].x,ps[idx[0]].y);idx.forEach(function(j){ctx.lineTo(ps[j].x,ps[j].y);});ctx.closePath();ctx.fillStyle='rgba(159,176,204,0.3)';ctx.globalAlpha=alpha;ctx.fill();ctx.strokeStyle='rgba(38,52,79,0.5)';ctx.lineWidth=0.4;ctx.stroke();ctx.globalAlpha=1;}
        faceP([0,1,2,3],0.8);faceP([4,5,1,0],0.6);faceP([5,6,2,1],0.4);
      })(ppts);
      var ah=tr.actual/maxV*85,ayT=base-ah;
      var apts=[t({x:tr.x-bw/2,y:ayT,z:0}),t({x:tr.x+bw/2,y:ayT,z:0}),t({x:tr.x+bw/2,y:ayT,z:depth}),t({x:tr.x-bw/2,y:ayT,z:depth}),
                t({x:tr.x-bw/2,y:base, z:0}),t({x:tr.x+bw/2,y:base, z:0}),t({x:tr.x+bw/2,y:base, z:depth}),t({x:tr.x-bw/2,y:base, z:depth})];
      if(!apts.every(function(p){return isFinite(p.x);}))return;
      (function(ps,col,name,planned,actual){
        function faceA(idx,alpha){ctx.beginPath();ctx.moveTo(ps[idx[0]].x,ps[idx[0]].y);idx.forEach(function(j){ctx.lineTo(ps[j].x,ps[j].y);});ctx.closePath();ctx.fillStyle=col;ctx.globalAlpha=alpha;ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.4;ctx.stroke();ctx.globalAlpha=1;}
        faceA([0,1,2,3],0.88);faceA([4,5,1,0],0.65);faceA([5,6,2,1],0.45);
        var variance=((actual-planned)/planned*100).toFixed(1);
        var lp=t({x:ps[0].x-(ps[0].x-ps[1].x)/2,y:ayT-10,z:0});
        if(isFinite(ps[0].x)){ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=col;ctx.textAlign='center';ctx.fillText((variance>0?'+':'')+variance+'%',(ps[0].x+ps[1].x)/2,(ps[0].y+ps[1].y)/2-8);ctx.font='7px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText(name,(ps[0].x+ps[1].x)/2,(ps[0].y+ps[1].y)/2+2);ctx.textAlign='left';}
      })(apts,tr.col,tr.name,tr.planned,tr.actual);
    });
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('Grey = planned  ·  Colored = actual',14,H-12);
  }

  /* ---------- 3.6 Overhead Absorption Rate — concentric gauge dials ---------- */
  function render_overhead3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    ctx.clearRect(0,0,W,H);
    var cx=W/2,cy=H/2+20;
    var rate=d.rate||0.941, target=d.target||1.00, prior=d.prior||0.960;
    var gauges=[
      {label:'Absorption Rate',val:rate,   min:0.7,max:1.1,R:74,col:'#e2b13c',lw:12},
      {label:'Target',         val:target, min:0.7,max:1.1,R:52,col:'#3fcaa6',lw:12},
      {label:'Prior Period',   val:prior,  min:0.7,max:1.1,R:30,col:'#4ea0ff',lw:12}
    ];
    var startA=Math.PI*0.75,endA=Math.PI*2.25;
    gauges.forEach(function(g){
      var range=g.max-g.min;
      var valA=startA+(g.val-g.min)/range*(endA-startA);
      ctx.beginPath();ctx.arc(cx,cy,g.R,startA,endA);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=g.lw;ctx.stroke();
      ctx.beginPath();ctx.arc(cx,cy,g.R,startA,valA);ctx.strokeStyle=g.col;ctx.lineWidth=g.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';
      var okA=startA+(1.0-g.min)/range*(endA-startA);
      ctx.beginPath();ctx.arc(cx,cy,g.R,okA-0.03,okA+0.03);ctx.strokeStyle='#3fcaa6';ctx.lineWidth=g.lw+4;ctx.stroke();
      ctx.beginPath();ctx.arc(cx+g.R*Math.cos(valA),cy+g.R*Math.sin(valA),5,0,Math.PI*2);ctx.fillStyle=g.col;ctx.fill();
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=g.col;ctx.textAlign='center';
      ctx.fillText(g.label+' '+g.val.toFixed(3),cx,cy-(g.R===74?88:g.R===52?68:48));ctx.textAlign='left';
    });
    ctx.textAlign='center';ctx.font='bold 11px SFMono-Regular,monospace';ctx.fillStyle='#e2b13c';
    ctx.fillText(Math.round(rate*100)+'%',cx,cy+6);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';
    ctx.fillText('Overhead absorption',cx,cy+20);ctx.textAlign='left';
  }

  /* ---------- 3.7 Cost Risk P80 — 3D histogram ---------- */
  function render_costrisk3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var bac=d.bac||24900000,mean=d.mean||27400000,sig=d.sig||900000;
    var bars=34,minV=bac*0.95,maxV=mean+sig*2.5,bw=4,depth=14;
    var p50val=d.p50||mean-sig*0.1, p80val=d.p80||mean+sig*0.42;
    var heights=[];
    for(var i=0;i<bars;i++){heights.push(gauss3(minV+(i+0.5)*(maxV-minV)/bars,mean,sig));}
    var maxH=Math.max.apply(null,heights)||1;
    heights.forEach(function(h,bi){
      (function(idx){
        var xval=minV+(idx+0.5)*(maxV-minV)/bars;
        var xpos=(idx/bars-0.5)*bw*bars;
        var col=xval>bac+sig?'#e0556b':xval>bac?'#e2b13c':'#4ea0ff';
        var bh=h/maxH*88,yT=55-bh,yB=55;
        function c3(dx,dy,dz){return t({x:xpos+dx,y:dy,z:dz});}
        var pts=[c3(-bw/2,yT,-depth/2),c3(bw/2,yT,-depth/2),c3(bw/2,yT,depth/2),c3(-bw/2,yT,depth/2),
                 c3(-bw/2,yB,-depth/2),c3(bw/2,yB,-depth/2),c3(bw/2,yB,depth/2),c3(-bw/2,yB,depth/2)];
        if(!pts.every(function(p){return isFinite(p.x);}))return;
        function face(idxA,alpha){ctx.beginPath();ctx.moveTo(pts[idxA[0]].x,pts[idxA[0]].y);idxA.forEach(function(j){ctx.lineTo(pts[j].x,pts[j].y);});ctx.closePath();ctx.fillStyle=col;ctx.globalAlpha=alpha;ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.3;ctx.stroke();ctx.globalAlpha=1;}
        face([0,1,2,3],0.88);face([4,5,1,0],0.65);face([5,6,2,1],0.45);
      })(bi);
    });
    [{label:'P50 $'+(p50val/1e6).toFixed(1)+'M',val:p50val,col:'#3fcaa6'},{label:'P80 $'+(p80val/1e6).toFixed(1)+'M',val:p80val,col:'#e0556b'}].forEach(function(mk){
      var xp=((mk.val-minV)/(maxV-minV)*bars-0.5)*bw;
      var pl1=t({x:xp,y:-38,z:-depth/2}),pl2=t({x:xp,y:55,z:-depth/2});
      if(!isFinite(pl1.x))return;
      ctx.beginPath();ctx.moveTo(pl1.x,pl1.y);ctx.lineTo(pl2.x,pl2.y);ctx.strokeStyle=mk.col;ctx.lineWidth=1.5;ctx.stroke();
      pillDraw(ctx,pl1.x,pl1.y-6,mk.label,mk.col);
    });
  }

  /* ---------- 3.8 Analogous Estimate — 3D scatter, no drag ---------- */
  function render_analogous3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var peers=d.peers||[
      {name:'Proj A',size:85000,cost:312,type:0,col:'#4ea0ff',current:false},
      {name:'Proj B',size:72000,cost:298,type:1,col:'#4ea0ff',current:false},
      {name:'Proj C',size:95000,cost:325,type:0,col:'#4ea0ff',current:false},
      {name:'Proj D',size:110000,cost:340,type:2,col:'#4ea0ff',current:false},
      {name:'Proj E',size:68000,cost:289,type:1,col:'#4ea0ff',current:false},
      {name:'Proj F',size:88000,cost:318,type:0,col:'#4ea0ff',current:false},
      {name:'THIS',  size:d.thisSize||92000,cost:d.thisCost||334,type:0,col:'#e0556b',current:true}
    ];
    var minSize=60000,maxSize=120000,minCost=280,maxCost=350;
    var meanCost=d.meanCost||313;
    peers.forEach(function(pr){
      var x=(pr.size-minSize)/(maxSize-minSize)*120-60;
      var y=-(pr.cost-minCost)/(maxCost-minCost)*80+30;
      var z=pr.type*20-20;
      var pp=t({x:x,y:y,z:z});
      if(!isFinite(pp.x))return;
      var fp=t({x:x,y:30,z:z});
      if(isFinite(fp.x)){ctx.beginPath();ctx.moveTo(pp.x,pp.y);ctx.lineTo(fp.x,fp.y);ctx.strokeStyle=pr.col+'44';ctx.lineWidth=0.7;ctx.stroke();}
      var r2=pr.current?7:4;
      ctx.beginPath();ctx.arc(pp.x,pp.y,r2,0,Math.PI*2);ctx.fillStyle=pr.col;ctx.globalAlpha=pr.current?1:0.65;ctx.fill();ctx.globalAlpha=1;
      if(pr.current){ctx.beginPath();ctx.arc(pp.x,pp.y,r2+4,0,Math.PI*2);ctx.strokeStyle='#e0556b88';ctx.lineWidth=1.5;ctx.stroke();pillDraw(ctx,pp.x,pp.y-18,'THIS PROJECT','#e0556b');}
    });
    var pl1=t({x:-60,y:-(meanCost-minCost)/(maxCost-minCost)*80+30,z:-30});
    var pl2=t({x:60,y:-(meanCost-minCost)/(maxCost-minCost)*80+30,z:-30});
    if(isFinite(pl1.x)){ctx.beginPath();ctx.moveTo(pl1.x,pl1.y);ctx.lineTo(pl2.x,pl2.y);ctx.strokeStyle='rgba(63,202,166,0.4)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#3fcaa6';ctx.fillText('Peer mean $'+meanCost+'/sqft',pl2.x+5,pl2.y);}
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('X: building size  Y: $/sqft  Z: project type',14,H-12);
  }

  /* ---------- 3.9 Parametric Cost Index — 3D multi-line ---------- */
  function render_parametric3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var history=d.history||[1.00,1.01,0.99,0.98,0.97,0.95,0.947];
    var models=d.models||['RS Means','ENR Index','CBRE Model'];
    var offsets=[-15,0,15];
    var consensus=d.consensus||0.947;
    var xSpan=110,n=history.length;
    function yv(v){return 50-(v-0.90)/0.14*85;}
    var modelOffsets=[-0.010, 0, 0.010];
    models.forEach(function(model,mi){
      var zOff=offsets[mi];
      var col=['#4ea0ff','#e2b13c','#9b6dff'][mi];
      var modelHist=history.map(function(v,i){return v+modelOffsets[mi];});
      for(var i=0;i<n-1;i++){
        var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
        var p1=t({x:x1,y:yv(modelHist[i]),z:zOff}),p2=t({x:x2,y:yv(modelHist[i+1]),z:zOff});
        if(!isFinite(p1.x))continue;
        ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle=col;ctx.lineWidth=1.8;ctx.stroke();
        ctx.beginPath();ctx.arc(p2.x,p2.y,2.5,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
      }
      var lp=t({x:((n-1)/(n-1)-0.5)*xSpan+8,y:yv(modelHist[n-1]),z:zOff});
      if(isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=col;ctx.fillText(model,lp.x,lp.y);}
    });
    var bp1=t({x:-xSpan/2,y:yv(1.0),z:-20}),bp2=t({x:xSpan/2,y:yv(1.0),z:-20});
    if(isFinite(bp1.x)){ctx.beginPath();ctx.moveTo(bp1.x,bp1.y);ctx.lineTo(bp2.x,bp2.y);ctx.strokeStyle='rgba(63,202,166,0.4)';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);}
    pillDraw(ctx,W/2,18,'Consensus index '+consensus,'#e2b13c');
  }

  /* ---------- 3.10 Inflation Adjustment — dual area surfaces (2D, no drag) ---------- */
  function render_inflation3d(ctx, W, H, m, rx, ry) {
    var d=m.data||{};
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return proj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var periods=d.periods||['Q1','Q2','Q3','Q4','Q5','Q6'];
    var nominal= d.nominal||[4200000,4380000,4520000,4710000,4890000,5040000];
    var adjusted=d.adjusted||[4200000,4310000,4390000,4520000,4650000,4760000];
    var n=periods.length,xSpan=120,maxV=d.maxV||5200000,base=55;
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-nominal[i]/maxV*90,y2=base-nominal[i+1]/maxV*90;
      var pts=[t({x:x1,y:y1,z:-15}),t({x:x2,y:y2,z:-15}),t({x:x2,y:base,z:-15}),t({x:x1,y:base,z:-15})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(224,85,107,0.12)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle='#e0556b';ctx.lineWidth=2;ctx.stroke();
      ctx.beginPath();ctx.arc(pts[1].x,pts[1].y,3,0,Math.PI*2);ctx.fillStyle='#e0556b';ctx.fill();
    }
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-adjusted[i]/maxV*90,y2=base-adjusted[i+1]/maxV*90;
      var pts=[t({x:x1,y:y1,z:12}),t({x:x2,y:y2,z:12}),t({x:x2,y:base,z:12}),t({x:x1,y:base,z:12})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(78,160,255,0.15)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle='#4ea0ff';ctx.lineWidth=2;ctx.stroke();
      ctx.beginPath();ctx.arc(pts[1].x,pts[1].y,3,0,Math.PI*2);ctx.fillStyle='#4ea0ff';ctx.fill();
      var lp=t({x:x1,y:base+8,z:0});
      if(isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='center';ctx.fillText(periods[i],lp.x,lp.y);ctx.textAlign='left';}
    }
    var lastX=((n-1)/(n-1)-0.5)*xSpan;
    var gp1=t({x:lastX,y:base-nominal[n-1]/maxV*90,z:-15});
    var gp2=t({x:lastX,y:base-adjusted[n-1]/maxV*90,z:12});
    if(isFinite(gp1.x)&&isFinite(gp2.x)){
      ctx.beginPath();ctx.moveTo(gp1.x,gp1.y);ctx.lineTo(gp2.x,gp2.y);ctx.strokeStyle='#e2b13c';ctx.lineWidth=1.5;ctx.stroke();
      var infPct=d.inflationPct||5.9;
      pillDraw(ctx,(gp1.x+gp2.x)/2+22,(gp1.y+gp2.y)/2,'Inflation +'+infPct+'%','#e2b13c');
    }
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('── Nominal',14,14);
    ctx.fillStyle='#4ea0ff';ctx.fillText('── Real (adjusted)',14,26);
  }


  /* ---------- Cat 4-12 shared helpers (verbatim from reference) ---------- */
  var prj = proj;
  function pill(ctx,x,y,text,col){
    ctx.font='bold 9px SFMono-Regular,monospace';
    var tw=ctx.measureText(text).width+10;
    if(ctx.roundRect)ctx.roundRect(x-tw/2,y-8,tw,16,4);else ctx.rect(x-tw/2,y-8,tw,16);
    ctx.fillStyle=col+'22';ctx.fill();ctx.strokeStyle=col+'77';ctx.lineWidth=0.8;ctx.stroke();
    ctx.fillStyle=col;ctx.textAlign='center';ctx.fillText(text,x,y+3);ctx.textAlign='left';
  }
  function axL(ctx,x,y,text,col,align){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=col||'#64748b';ctx.textAlign=align||'center';ctx.fillText(text,x,y);ctx.textAlign='left';}
  function aL(ctx,x,y,t,col,align){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=col||'#64748b';ctx.textAlign=align||'left';ctx.fillText(t,x,y);ctx.textAlign='left';}
  function yAxis(ctx,PAD,CH,ticks){
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
    ticks.forEach(function(tk){var y=PAD.t+CH-tk.pct*CH;axL(ctx,PAD.l-4,y+3,tk.label,'#64748b','right');ctx.beginPath();ctx.moveTo(PAD.l-3,y);ctx.lineTo(PAD.l,y);ctx.strokeStyle='rgba(38,52,79,0.5)';ctx.lineWidth=0.5;ctx.stroke();});
  }
  function T(p,rx,ry,fov,cx,cy){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
  var SC={Red:'#e0556b',Amber:'#e2b13c',Green:'#3fcaa6',Yellow:'#f0c040',null:'#26344f'};

  /* CAT 4-5 RENDERERS (verbatim) */
  // ═══════════════ CAT 4 RENDERERS ═══════════════════════════

  // 4.1 Document Risk — 2D radar
  function render_41(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var cx=W/2,cy=H/2+8,R=62;
    var dims=[{label:'RFI Density',val:0.55,col:'#e2b13c'},{label:'Dispute Lang',val:0.70,col:'#e0556b'},{label:'Change Orders',val:0.40,col:'#e2b13c'},{label:'NCR Rate',val:0.30,col:'#3fcaa6'},{label:'Submittal Rej',val:0.35,col:'#3fcaa6'},{label:'OAC Issues',val:0.60,col:'#e2b13c'}];
    var n=dims.length;
    [0.30,0.70,1.0].forEach(function(th,ti){
      var col=['#3fcaa6','#e2b13c','#e0556b'][ti];
      ctx.beginPath();
      for(var i=0;i<=n;i++){var a=(i/n)*Math.PI*2-Math.PI/2;i===0?ctx.moveTo(cx+th*R*Math.cos(a),cy+th*R*Math.sin(a)):ctx.lineTo(cx+th*R*Math.cos(a),cy+th*R*Math.sin(a));}
      ctx.closePath();ctx.strokeStyle=col+'44';ctx.lineWidth=0.7;ctx.stroke();ctx.fillStyle=col+'08';ctx.fill();
    });
    dims.forEach(function(d,i){
      var a=(i/n)*Math.PI*2-Math.PI/2;
      ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+R*Math.cos(a),cy+R*Math.sin(a));ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
      var lx=cx+(R+18)*Math.cos(a),ly=cy+(R+18)*Math.sin(a);
      ctx.font='8px SFMono-Regular,monospace';var tw=ctx.measureText(d.label).width+8;
      if(ctx.roundRect)ctx.roundRect(lx-tw/2,ly-7,tw,14,3);else ctx.rect(lx-tw/2,ly-7,tw,14);
      ctx.fillStyle=d.col+'18';ctx.fill();ctx.strokeStyle=d.col+'44';ctx.lineWidth=0.7;ctx.stroke();
      ctx.fillStyle=d.col;ctx.textAlign='center';ctx.fillText(d.label,lx,ly+3);ctx.textAlign='left';
    });
    ctx.beginPath();
    dims.forEach(function(d,i){var a=(i/n)*Math.PI*2-Math.PI/2;var r=d.val*R;i===0?ctx.moveTo(cx+r*Math.cos(a),cy+r*Math.sin(a)):ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a));});
    ctx.closePath();ctx.fillStyle='rgba(226,177,60,0.18)';ctx.fill();ctx.strokeStyle='#e2b13c';ctx.lineWidth=1.8;ctx.stroke();
    dims.forEach(function(d,i){var a=(i/n)*Math.PI*2-Math.PI/2;ctx.beginPath();ctx.arc(cx+d.val*R*Math.cos(a),cy+d.val*R*Math.sin(a),3.5,0,Math.PI*2);ctx.fillStyle=d.col;ctx.fill();});
    ctx.textAlign='center';ctx.font='bold 12px SFMono-Regular,monospace';ctx.fillStyle='#e2b13c';ctx.fillText('0.45',cx,cy+4);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('risk score',cx,cy+16);ctx.textAlign='left';
  }

  // 4.2 RFI Velocity — 3D line + velocity band
  function render_42(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var rfiPerWk=[1.2,1.5,1.8,2.4,3.0,3.2],respDays=[8,10,12,15,18,18];
    var n=rfiPerWk.length,xSpan=110;
    function yrfi(v){return 38-(v-1)/2.5*72;}
    function yresp(v){return 38-(v-8)/12*72;}
    // Response time band (back, faint)
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var pts=[t({x:x1,y:yresp(respDays[i]),z:-18}),t({x:x2,y:yresp(respDays[i+1]),z:-18}),t({x:x2,y:38,z:-18}),t({x:x1,y:38,z:-18})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(159,176,204,0.1)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle='rgba(159,176,204,0.5)';ctx.lineWidth=1.5;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    }
    // RFI velocity line (front)
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var col=rfiPerWk[i+1]>2.5?'#e0556b':'#e2b13c';
      var p1=t({x:x1,y:yrfi(rfiPerWk[i]),z:12}),p2=t({x:x2,y:yrfi(rfiPerWk[i+1]),z:12});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
      var lp=t({x:(x1+x2)/2,y:38+10,z:0});
      if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,'M'+(i+1),'#64748b','center');
    }
    // Threshold
    var tp1=t({x:-xSpan/2,y:yrfi(2.5),z:-12}),tp2=t({x:xSpan/2,y:yrfi(2.5),z:-12});
    if(isFinite(tp1.x)){ctx.beginPath();ctx.moveTo(tp1.x,tp1.y);ctx.lineTo(tp2.x,tp2.y);ctx.strokeStyle='#e0556b77';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);axL(ctx,tp2.x+3,tp2.y,'2.5/wk threshold','#e0556b','left');}
    var lp=t({x:xSpan/4,y:yrfi(rfiPerWk[n-1]),z:12});
    if(isFinite(lp.x)) pill(ctx,lp.x,lp.y-15,'3.2 RFIs/wk','#e0556b');
    yAxis(ctx,PAD,CH,[{pct:0,label:'1.0'},{pct:0.5,label:'2.3'},{pct:1.0,label:'3.5'}]);
    axL(ctx,W/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'RFIs per week','#64748b','center');ctx.restore();
  }

  // 4.3 Submittal Rejection Rate — 3D area
  function render_43(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var rates=[0.08,0.10,0.12,0.14,0.15,0.13],n=rates.length,xSpan=110,base=42;
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-rates[i]*280,y2=base-rates[i+1]*280;
      var col=rates[i+1]>0.12?'#e0556b':'#e2b13c';
      var pts=[t({x:x1,y:y1,z:12}),t({x:x2,y:y2,z:12}),t({x:x2,y:base,z:12}),t({x:x1,y:base,z:12})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle=col+'28';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(pts[0].x,pts[0].y,3,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
      var lp=t({x:(x1+x2)/2,y:base+10,z:0});if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,'M'+(i+1),'#64748b','center');
    }
    var tp1=t({x:-xSpan/2,y:base-0.10*280,z:-16}),tp2=t({x:xSpan/2,y:base-0.10*280,z:-16});
    if(isFinite(tp1.x)){ctx.beginPath();ctx.moveTo(tp1.x,tp1.y);ctx.lineTo(tp2.x,tp2.y);ctx.strokeStyle='#e0556b77';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);axL(ctx,tp2.x+3,tp2.y,'10% threshold','#e0556b','left');}
    pill(ctx,W*0.65,28,'15% peak','#e0556b');
    yAxis(ctx,PAD,CH,[{pct:0,label:'0%'},{pct:0.57,label:'10%'},{pct:1.0,label:'18%'}]);
    axL(ctx,W/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'Rejection rate','#64748b','center');ctx.restore();
  }

  // 4.4 NCR Rate — 2D histogram
  function render_44(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var PAD={l:40,r:14,t:20,b:32};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var periods=['M1','M2','M3','M4','M5','M6'],ncrs=[2,3,4,5,4,6];
    var n=periods.length,bw=CW/n*0.65,gap=CW/n;
    var maxV=7;
    // Grid
    [2,4,6].forEach(function(v){var y=PAD.t+CH-v/maxV*CH;ctx.beginPath();ctx.moveTo(PAD.l,y);ctx.lineTo(PAD.l+CW,y);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();axL(ctx,PAD.l-4,y+3,''+v,'#64748b','right');});
    // Bars
    ncrs.forEach(function(v,i){
      var x=PAD.l+i*gap+gap/2-bw/2;
      var bh=v/maxV*CH;
      var y=PAD.t+CH-bh;
      var col=v>=5?'#e0556b':v>=3?'#e2b13c':'#3fcaa6';
      ctx.fillStyle=col;ctx.globalAlpha=0.88;ctx.fillRect(x,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.3)';ctx.lineWidth=0.4;ctx.strokeRect(x,y,bw,bh);
      axL(ctx,x+bw/2,PAD.t+CH+12,periods[i],'#64748b','center');
      ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=col;ctx.textAlign='center';ctx.fillText(v,x+bw/2,y-4);ctx.textAlign='left';
    });
    // Threshold
    var thresh=4,ty=PAD.t+CH-thresh/maxV*CH;
    ctx.beginPath();ctx.moveTo(PAD.l,ty);ctx.lineTo(PAD.l+CW,ty);ctx.strokeStyle='#e0556b77';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    axL(ctx,PAD.l+CW+3,ty,'threshold 4','#e0556b','left');
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
    axL(ctx,W/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'NCR count','#64748b','center');ctx.restore();
  }

  // 4.5 Weather Day Impact — 3D area
  function render_45(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var lost=[0,1,2,4,4,5],buffer=[5,5,5,5,4,3],n=lost.length,xSpan=110,base=42;
    // Buffer area (back)
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-buffer[i]/6*80,y2=base-buffer[i+1]/6*80;
      var pts=[t({x:x1,y:y1,z:-18}),t({x:x2,y:y2,z:-18}),t({x:x2,y:base,z:-18}),t({x:x1,y:base,z:-18})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(63,202,166,0.1)';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle='#3fcaa699';ctx.lineWidth=1.5;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    }
    // Lost days area (front)
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=base-lost[i]/6*80,y2=base-lost[i+1]/6*80;
      var col=lost[i+1]>=buffer[i+1]?'#e0556b':'#e2b13c';
      var pts=[t({x:x1,y:y1,z:12}),t({x:x2,y:y2,z:12}),t({x:x2,y:base,z:12}),t({x:x1,y:base,z:12})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle=col+'28';ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      var lp=t({x:(x1+x2)/2,y:base+10,z:0});if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,'M'+(i+1),'#64748b','center');
    }
    pill(ctx,W*0.7,26,'Buffer 3d remaining','#e2b13c');
    yAxis(ctx,PAD,CH,[{pct:0,label:'0d'},{pct:0.5,label:'3d'},{pct:1.0,label:'6d'}]);
    axL(ctx,W/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'Weather days','#64748b','center');ctx.restore();
  }

  // 4.6 Change Order Frequency — 3D dual line
  function render_46(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:50,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var count=[0,1,0,2,1,3],value=[0,85000,0,210000,95000,380000];
    var n=count.length,xSpan=105;
    function yc(v){return 38-v/3.5*72;}
    function yv(v){return 38-v/400000*72;}
    // Count line (front)
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:yc(count[i]),z:14}),p2=t({x:x2,y:yc(count[i+1]),z:14});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e2b13c';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#e2b13c';ctx.fill();
    }
    // Value line (back)
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:yv(value[i]),z:-14}),p2=t({x:x2,y:yv(value[i+1]),z:-14});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e0556b';ctx.lineWidth=2;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#e0556b';ctx.fill();
    }
    // Labels at right
    var lc=t({x:xSpan/2+4,y:yc(count[n-1]),z:14}),lv=t({x:xSpan/2+4,y:yv(value[n-1]),z:-14});
    if(isFinite(lc.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#e2b13c';ctx.fillText('Count',lc.x,lc.y);}
    if(isFinite(lv.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('Value',lv.x,lv.y);}
    // Period labels
    for(var i=0;i<n;i++){var lp=t({x:(i/(n-1)-0.5)*xSpan,y:38+10,z:0});if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,'M'+(i+1),'#64748b','center');}
    pill(ctx,W*0.6,22,'$380k cumulative','#e0556b');
    yAxis(ctx,PAD,CH,[{pct:0,label:'0'},{pct:0.5,label:'2'},{pct:1.0,label:'4'}]);
    axL(ctx,PAD.l+CW/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'CO count / value','#64748b','center');ctx.restore();
  }

  // 4.7 Dispute Escalation Index — 3D line + threshold
  function render_47(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var idx=[0.12,0.18,0.24,0.30,0.35,0.38],n=idx.length,xSpan=110;
    function yv(v){return 40-(v/0.6)*80;}
    // Uncertainty band
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var y1=yv(idx[i]),y2=yv(idx[i+1]),band=2.5;
      var pts=[t({x:x1,y:y1-band,z:0}),t({x:x2,y:y2-band,z:0}),t({x:x2,y:y2+band,z:0}),t({x:x1,y:y1+band,z:0})];
      if(!pts.every(function(p){return isFinite(p.x);}))continue;
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(224,85,107,0.1)';ctx.fill();
    }
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var p1=t({x:x1,y:yv(idx[i]),z:0}),p2=t({x:x2,y:yv(idx[i+1]),z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e0556b';ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle='#e0556b';ctx.fill();
      var lp=t({x:(x1+x2)/2,y:yv(0)+12,z:0});if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,'M'+(i+1),'#64748b','center');
    }
    var tp1=t({x:-xSpan/2,y:yv(0.30),z:-18}),tp2=t({x:xSpan/2,y:yv(0.30),z:-18});
    if(isFinite(tp1.x)){ctx.beginPath();ctx.moveTo(tp1.x,tp1.y);ctx.lineTo(tp2.x,tp2.y);ctx.strokeStyle='#e0556b77';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);axL(ctx,tp2.x+3,tp2.y,'Escalation threshold 0.30','#e0556b','left');}
    var lp=t({x:xSpan/4,y:yv(idx[n-1]),z:0});if(isFinite(lp.x)) pill(ctx,lp.x,lp.y-15,'Index 0.38','#e0556b');
    yAxis(ctx,PAD,CH,[{pct:0,label:'0.00'},{pct:0.5,label:'0.30'},{pct:1.0,label:'0.60'}]);
    axL(ctx,W/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'Dispute index','#64748b','center');ctx.restore();
  }

  // 4.8 Subcontractor Performance — 2D radar
  function render_48(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var cx=W/2,cy=H/2+5,R=58;
    var subs=[
      {name:'Elec',scores:[0.72,0.65,0.80,0.70,0.60],col:'#4ea0ff'},
      {name:'Mech',scores:[0.55,0.60,0.65,0.50,0.58],col:'#e2b13c'},
      {name:'Civil',scores:[0.80,0.75,0.85,0.78,0.72],col:'#3fcaa6'}
    ];
    var dims=['Schedule','Quality','Safety','Cost','Comm'],n=dims.length;
    // Grid rings
    [0.33,0.66,1.0].forEach(function(th){
      ctx.beginPath();
      for(var i=0;i<=n;i++){var a=(i/n)*Math.PI*2-Math.PI/2;i===0?ctx.moveTo(cx+th*R*Math.cos(a),cy+th*R*Math.sin(a)):ctx.lineTo(cx+th*R*Math.cos(a),cy+th*R*Math.sin(a));}
      ctx.closePath();ctx.strokeStyle='rgba(38,52,79,0.45)';ctx.lineWidth=0.6;ctx.stroke();
    });
    // Spokes + labels
    dims.forEach(function(d,i){
      var a=(i/n)*Math.PI*2-Math.PI/2;
      ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+R*Math.cos(a),cy+R*Math.sin(a));ctx.strokeStyle='rgba(38,52,79,0.5)';ctx.lineWidth=0.5;ctx.stroke();
      axL(ctx,cx+(R+14)*Math.cos(a),cy+(R+14)*Math.sin(a)+3,d,'#64748b','center');
    });
    // Sub polygons
    subs.forEach(function(sub){
      ctx.beginPath();
      sub.scores.forEach(function(v,i){var a=(i/n)*Math.PI*2-Math.PI/2;var r=v*R;i===0?ctx.moveTo(cx+r*Math.cos(a),cy+r*Math.sin(a)):ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a));});
      ctx.closePath();ctx.fillStyle=sub.col+'18';ctx.fill();ctx.strokeStyle=sub.col;ctx.lineWidth=1.6;ctx.stroke();
    });
    // Legend
    subs.forEach(function(sub,i){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=sub.col;ctx.fillText('── '+sub.name,14,H-28+i*12);});
  }

  // 4.9 Procurement Lead Time — 3D paired dots
  function render_49(ctx,W,H,m,rx,ry){
    var PAD={l:70,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var items=[
      {name:'Steel',planned:45,actual:52,col:'#e0556b'},
      {name:'HVAC',planned:60,actual:72,col:'#e0556b'},
      {name:'Elec panels',planned:30,actual:35,col:'#e2b13c'},
      {name:'Concrete',planned:14,actual:13,col:'#3fcaa6'},
      {name:'Glazing',planned:40,actual:46,col:'#e2b13c'}
    ];
    var maxV=80,xSpan=100;
    function xForV(v){return (v/maxV-0.5)*xSpan;}
    items.forEach(function(item,i){
      var y=(i/(items.length-1)-0.5)*70;
      // Connector line
      var pp=t({x:xForV(item.planned),y:y,z:-10}),pa=t({x:xForV(item.actual),y:y,z:10});
      if(!isFinite(pp.x)||!isFinite(pa.x))return;
      ctx.beginPath();ctx.moveTo(pp.x,pp.y);ctx.lineTo(pa.x,pa.y);ctx.strokeStyle='rgba(100,116,139,0.4)';ctx.lineWidth=1.5;ctx.stroke();
      // Planned dot (grey)
      ctx.beginPath();ctx.arc(pp.x,pp.y,5,0,Math.PI*2);ctx.fillStyle='rgba(159,176,204,0.6)';ctx.fill();
      // Actual dot (colored)
      ctx.beginPath();ctx.arc(pa.x,pa.y,5,0,Math.PI*2);ctx.fillStyle=item.col;ctx.fill();
      // Label on left
      var lp=t({x:-xSpan/2-8,y:y,z:0});if(isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(item.name,lp.x,lp.y+3);ctx.textAlign='left';}
      // Value label on actual
      ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=item.col;ctx.textAlign='center';
      ctx.fillText(item.actual+'d',pa.x,pa.y-8);ctx.textAlign='left';
    });
    // X axis ticks
    [0,20,40,60,80].forEach(function(v){
      var lp=t({x:xForV(v),y:40,z:0});if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,v+'d','#64748b','center');
    });
    pill(ctx,W*0.65,20,'● Planned  ● Actual','#64748b');
    axL(ctx,W/2,H-4,'Lead time (days)','#64748b','center');
  }

  // 4.10 Spec Conflict Index — 2D chord
  function render_410(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var cx=W/2,cy=H/2+5,R=65;
    var docs=['Arch Drwgs','Struct Spec','MEP Spec','Civil Spec','Geotech'];
    var n=docs.length;
    var conflicts=[[0,0.7,0.5,0.2,0.1],[0.3,0,0.8,0.4,0.1],[0.2,0.4,0,0.6,0.2],[0.1,0.2,0.3,0,0.1],[0.1,0.1,0.2,0.1,0]];
    var cols=['#4ea0ff','#e0556b','#e2b13c','#3fcaa6','#9b6dff'];
    docs.forEach(function(d,i){
      var a0=(i/n)*Math.PI*2-Math.PI/2,a1=((i+0.82)/n)*Math.PI*2-Math.PI/2;
      ctx.beginPath();ctx.arc(cx,cy,R,a0,a1);ctx.strokeStyle=cols[i];ctx.lineWidth=14;ctx.stroke();
      var midA=(a0+a1)/2;
      ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=cols[i];ctx.textAlign='center';
      ctx.fillText(d,cx+(R+20)*Math.cos(midA),cy+(R+20)*Math.sin(midA)+3);ctx.textAlign='left';
    });
    for(var i=0;i<n;i++){
      for(var j=i+1;j<n;j++){
        var v=Math.max(conflicts[i][j],conflicts[j][i]);
        if(v<0.2)continue;
        var a1=(i/n+0.41/n)*Math.PI*2-Math.PI/2,a2=(j/n+0.41/n)*Math.PI*2-Math.PI/2;
        var x1=cx+R*Math.cos(a1),y1=cy+R*Math.sin(a1),x2=cx+R*Math.cos(a2),y2=cy+R*Math.sin(a2);
        ctx.beginPath();ctx.moveTo(x1,y1);ctx.bezierCurveTo(cx+(x1-cx)*0.25,cy+(y1-cy)*0.25,cx+(x2-cx)*0.25,cy+(y2-cy)*0.25,x2,y2);
        var col=v>0.6?'#e0556b':v>0.3?'#e2b13c':'#4ea0ff';
        ctx.strokeStyle=col;ctx.lineWidth=v*4;ctx.globalAlpha=0.6;ctx.stroke();ctx.globalAlpha=1;
      }
    }
    pill(ctx,W/2,18,'MEP–Struct conflict 0.8','#e0556b');
    ctx.font='8px SFMono-Regular,monospace';
    [{col:'#e0556b',label:'>0.6 conflict'},{col:'#e2b13c',label:'0.3–0.6'},{col:'#4ea0ff',label:'<0.3'}].forEach(function(l,i){ctx.fillStyle=l.col;ctx.fillText('─ '+l.label,14,H-28+i*12);});
  }

  // ═══════════════ CAT 5 RENDERERS ═══════════════════════════

  // 5.1 DSM Propagation — 3D network cascade
  function render_51(ctx,W,H,m,rx,ry){
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var layers=[
      [{id:'Arch',x:0,y:-50,z:0,col:'#e0556b',trigger:true}],
      [{id:'Struct',x:-35,y:-15,z:-18,col:'#e2b13c',rework:0.8},{id:'MEP',x:35,y:-15,z:18,col:'#e2b13c',rework:0.6}],
      [{id:'Civil',x:-50,y:20,z:-10,col:'#f0c040',rework:0.4},{id:'Elec',x:0,y:20,z:0,col:'#f0c040',rework:0.5},{id:'Finishes',x:50,y:20,z:10,col:'#f0c040',rework:0.3}],
      [{id:'Closeout',x:0,y:52,z:0,col:'#3fcaa6',rework:0.2}]
    ];
    var nodes={};layers.forEach(function(l){l.forEach(function(n){nodes[n.id]=n;});});
    var edges=[['Arch','Struct',0.8],['Arch','MEP',0.6],['Struct','Civil',0.4],['Struct','Elec',0.5],['MEP','Elec',0.7],['MEP','Finishes',0.3],['Elec','Closeout',0.2],['Finishes','Closeout',0.2]];
    // Edges
    edges.forEach(function(e){
      var n1=nodes[e[0]],n2=nodes[e[1]];
      var p1=t(n1),p2=t(n2);if(!isFinite(p1.x))return;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle=e[2]>0.6?'#e0556b88':e[2]>0.3?'#e2b13c66':'rgba(100,116,139,0.4)';
      ctx.lineWidth=e[2]*3+0.5;ctx.stroke();
      var mx=(p1.x+p2.x)/2,my=(p1.y+p2.y)/2,ang=Math.atan2(p2.y-p1.y,p2.x-p1.x);
      ctx.save();ctx.translate(mx,my);ctx.rotate(ang);ctx.beginPath();ctx.moveTo(-4,-3);ctx.lineTo(4,0);ctx.lineTo(-4,3);ctx.fillStyle=e[2]>0.6?'#e0556b':'#e2b13c';ctx.fill();ctx.restore();
    });
    // Nodes
    layers.forEach(function(l){l.forEach(function(n){
      var p=t(n);if(!isFinite(p.x))return;
      var r=Math.max(12,16*p.s);
      ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fillStyle=n.col+'22';ctx.fill();ctx.strokeStyle=n.col;ctx.lineWidth=n.trigger?2.5:1.8;ctx.stroke();
      ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=n.col;ctx.textAlign='center';ctx.fillText(n.id,p.x,p.y+3);ctx.textAlign='left';
      if(n.rework){
        var rp=t({x:n.x+r+2,y:n.y-r-2,z:n.z});
        if(isFinite(rp.x)){ctx.font='7px SFMono-Regular,monospace';ctx.fillStyle=n.col;ctx.fillText(Math.round(n.rework*100)+'%',rp.x,rp.y);}
      }
    });});
    axL(ctx,W/2,H-8,'Arrow width = rework magnitude · Red = trigger source','#64748b','center');
  }

  // 5.2 Sensitivity Analysis — 2D tornado
  function render_52(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var PAD={l:88,r:50,t:20,b:28};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var vars=[
      {name:'Labor rate',    low:-8.2, high:12.4,col:'#e0556b'},
      {name:'Material cost', low:-6.1, high:9.8, col:'#e0556b'},
      {name:'Productivity',  low:-5.5, high:7.2, col:'#e2b13c'},
      {name:'Schedule slip', low:-4.8, high:6.5, col:'#e2b13c'},
      {name:'Contingency',   low:-3.2, high:4.1, col:'#f0c040'}
    ];
    var n=vars.length,bh=CH/n*0.58,gap=CH/n,maxV=14;
    var cx=PAD.l+(-0)/maxV*CW; // center line at 0
    var zeroX=PAD.l+CW/2;
    // Grid
    [-10,-5,0,5,10].forEach(function(v){
      var x=zeroX+v/maxV*CW;
      ctx.beginPath();ctx.moveTo(x,PAD.t);ctx.lineTo(x,PAD.t+CH);
      ctx.strokeStyle='rgba(38,52,79,0.35)';ctx.lineWidth=0.4;ctx.stroke();
      axL(ctx,x,PAD.t+CH+12,v+'%','#64748b','center');
    });
    // Zero line
    ctx.beginPath();ctx.moveTo(zeroX,PAD.t-4);ctx.lineTo(zeroX,PAD.t+CH);
    ctx.strokeStyle='rgba(100,116,139,0.6)';ctx.lineWidth=0.8;ctx.stroke();
    // Bars
    vars.forEach(function(v,i){
      var y=PAD.t+i*gap+gap/2-bh/2;
      // Low bar (left of zero)
      var lowW=Math.abs(v.low)/maxV*CW;
      ctx.fillStyle='rgba(78,160,255,0.55)';ctx.globalAlpha=0.9;
      ctx.fillRect(zeroX-lowW,y,lowW,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.25)';ctx.lineWidth=0.4;ctx.strokeRect(zeroX-lowW,y,lowW,bh);
      // High bar (right of zero)
      var highW=v.high/maxV*CW;
      ctx.fillStyle=v.col;ctx.globalAlpha=0.85;
      ctx.fillRect(zeroX,y,highW,bh);ctx.globalAlpha=1;
      ctx.strokeRect(zeroX,y,highW,bh);
      // Labels
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';
      ctx.fillText(v.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.font='bold 8px SFMono-Regular,monospace';
      ctx.fillStyle='#4ea0ff';ctx.textAlign='right';ctx.fillText(v.low+'%',zeroX-lowW-3,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=v.col;ctx.fillText('+'+v.high+'%',zeroX+highW+3,y+bh/2+3);
    });
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.5;ctx.stroke();
    axL(ctx,PAD.l+CW/2,H-4,'EAC impact (%)','#64748b','center');
  }

  // 5.3 Tornado Ranking — 2D horizontal
  function render_53(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var PAD={l:90,r:40,t:20,b:16};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var vars=[
      {name:'Labor rate',impact:12.4,col:'#e0556b'},
      {name:'Material cost',impact:9.8,col:'#e0556b'},
      {name:'Productivity',impact:7.2,col:'#e2b13c'},
      {name:'Schedule slip',impact:6.5,col:'#e2b13c'},
      {name:'Contingency',impact:4.1,col:'#f0c040'},
      {name:'Overhead',impact:2.8,col:'#3fcaa6'}
    ];
    var n=vars.length,bh=CH/n*0.62,gap=CH/n,maxV=14;
    vars.forEach(function(v,i){
      var y=PAD.t+i*gap+gap/2-bh/2;
      var bw=v.impact/maxV*CW;
      var col=v.col;
      ctx.fillStyle=col;ctx.globalAlpha=0.85;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.25)';ctx.lineWidth=0.4;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(v.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=col;ctx.fillText('+'+v.impact+'%',PAD.l+bw+4,y+bh/2+3);
    });
    // Grid lines
    [5,10].forEach(function(v){var x=PAD.l+v/maxV*CW;ctx.beginPath();ctx.moveTo(x,PAD.t);ctx.lineTo(x,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.35)';ctx.lineWidth=0.4;ctx.stroke();axL(ctx,x,PAD.t+CH+12,v+'%','#64748b','center');});
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
    axL(ctx,PAD.l+CW/2,H-4,'EAC impact (%)','#64748b','center');
  }

  // 5.4 Scenario Modeling — 3D overlapping distributions
  function render_54(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2+5,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    function gauss(x,mu,sig){return Math.exp(-0.5*Math.pow((x-mu)/sig,2));}
    var scenarios=[
      {name:'Optimistic',mu:25800000,sig:600000,col:'#3fcaa6',z:-22},
      {name:'Base',      mu:27100000,sig:900000,col:'#e2b13c',z:0},
      {name:'Pessimistic',mu:28600000,sig:1100000,col:'#e0556b',z:22}
    ];
    var minV=23500000,maxV=31000000,bars=40,bw=3.5,depth=10;
    scenarios.forEach(function(sc){
      var heights=[];
      for(var i=0;i<bars;i++) heights.push(gauss(minV+(i+0.5)*(maxV-minV)/bars,sc.mu,sc.sig));
      var maxH=Math.max.apply(null,heights);
      heights.forEach(function(h,i){
        var xpos=(i/bars-0.5)*bw*bars;
        var bh=h/maxH*70,yT=40-bh,yB=40;
        function c3(dx,dy,dz){return t({x:xpos+dx,y:dy,z:sc.z+dz});}
        var pts=[c3(-bw/2,yT,-depth/2),c3(bw/2,yT,-depth/2),c3(bw/2,yT,depth/2),c3(-bw/2,yT,depth/2),
                 c3(-bw/2,yB,-depth/2),c3(bw/2,yB,-depth/2),c3(bw/2,yB,depth/2),c3(-bw/2,yB,depth/2)];
        if(!pts.every(function(p){return isFinite(p.x);}))return;
        function face(idx,alpha){ctx.beginPath();ctx.moveTo(pts[idx[0]].x,pts[idx[0]].y);idx.forEach(function(j){ctx.lineTo(pts[j].x,pts[j].y);});ctx.closePath();ctx.fillStyle=sc.col;ctx.globalAlpha=alpha*0.75;ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.stroke();ctx.globalAlpha=1;}
        face([0,1,2,3],0.88);face([4,5,1,0],0.6);face([5,6,2,1],0.4);
      });
      // Peak label
      var peakI=heights.indexOf(Math.max.apply(null,heights));
      var peakX=(peakI/bars-0.5)*bw*bars;
      var lp=t({x:peakX,y:-32,z:sc.z});
      if(isFinite(lp.x)){ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=sc.col;ctx.textAlign='center';ctx.fillText(sc.name,lp.x,lp.y);ctx.fillText('$'+(sc.mu/1e6).toFixed(1)+'M',lp.x,lp.y+10);ctx.textAlign='left';}
    });
    yAxis(ctx,PAD,CH,[{pct:0,label:'0'},{pct:0.5,label:'50%'},{pct:1.0,label:'100%'}]);
    axL(ctx,W/2,H-4,'EAC ($M)','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'Probability','#64748b','center');ctx.restore();
  }

  // 5.5 Rework Feedback Loop — 3D spiral
  function render_55(ctx,W,H,m,rx,ry){
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    // Spiral: each loop = one feedback cycle, radius grows with amplification
    var loops=4,stepsPerLoop=40,totalSteps=loops*stepsPerLoop;
    var prevPt=null;
    for(var i=0;i<totalSteps;i++){
      var angle=(i/stepsPerLoop)*Math.PI*2;
      var loop=i/stepsPerLoop;
      var r=12+loop*18;
      var amp=1+loop*0.35;
      var y=-loop*20+30;
      var x=r*Math.cos(angle);
      var z=r*Math.sin(angle);
      var pp=t({x:x,y:y,z:z});
      if(prevPt&&isFinite(pp.x)&&isFinite(prevPt.x)){
        var col=amp>2.0?'#e0556b':amp>1.5?'#e2b13c':'#4ea0ff';
        ctx.beginPath();ctx.moveTo(prevPt.x,prevPt.y);ctx.lineTo(pp.x,pp.y);
        ctx.strokeStyle=col;ctx.lineWidth=1.5+loop*0.3;ctx.stroke();
      }
      prevPt=pp;
    }
    // Loop labels
    for(var loop=0;loop<loops;loop++){
      var y=-loop*20+30,r2=12+loop*18;
      var lp=t({x:r2+12,y:y,z:0});
      if(isFinite(lp.x)){
        ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=loop>=2?'#e0556b':'#e2b13c';
        ctx.fillText('Loop '+(loop+1)+' ×'+(1+loop*0.35).toFixed(2),lp.x,lp.y+3);
      }
    }
    // Center
    ctx.beginPath();ctx.arc(cx,cy+5-30*0,5,0,Math.PI*2);ctx.fillStyle='#e9a23b';ctx.fill();
    axL(ctx,W/2,H-8,'Spiral radius = amplification  ·  Color = severity','#64748b','center');
  }

  // 5.6 Queueing Bottleneck — 3D area
  function render_56(ctx,W,H,m,rx,ry){
    var PAD={l:40,r:14,t:18,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var cx=PAD.l+CW/2,cy=PAD.t+CH/2,fov=Math.min(CW,CH)*0.9;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var queues=[
      {name:'Design review',depth:[2,4,7,10,8,6],col:'#4ea0ff'},
      {name:'RFI response', depth:[1,3,5,8,12,10],col:'#e2b13c'},
      {name:'Submittal Q',  depth:[0,2,4,6,9,11],col:'#e0556b'}
    ];
    var n=6,xSpan=110,base=42,maxD=13;
    queues.forEach(function(q,qi){
      var z=(qi-1)*16;
      for(var i=0;i<n-1;i++){
        var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
        var y1=base-q.depth[i]/maxD*80,y2=base-q.depth[i+1]/maxD*80;
        var pts=[t({x:x1,y:y1,z:z}),t({x:x2,y:y2,z:z}),t({x:x2,y:base,z:z}),t({x:x1,y:base,z:z})];
        if(!pts.every(function(p){return isFinite(p.x);}))continue;
        ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);pts.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle=q.col+'25';ctx.fill();
        ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);ctx.strokeStyle=q.col;ctx.lineWidth=2;ctx.stroke();
      }
      var lp=t({x:xSpan/4,y:base-q.depth[n-1]/maxD*80-8,z:z});
      if(isFinite(lp.x)){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle=q.col;ctx.fillText(q.name,lp.x,lp.y);}
    });
    for(var i=0;i<n;i++){var lp=t({x:(i/(n-1)-0.5)*xSpan,y:base+10,z:0});if(isFinite(lp.x)) axL(ctx,lp.x,lp.y,'M'+(i+1),'#64748b','center');}
    yAxis(ctx,PAD,CH,[{pct:0,label:'0'},{pct:0.46,label:'6'},{pct:1.0,label:'13'}]);
    axL(ctx,W/2,H-4,'Reporting period','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);axL(ctx,0,0,'Queue depth','#64748b','center');ctx.restore();
  }

  // 5.7 Agent-Based Supply — 3D network nodes
  function render_57(ctx,W,H,m,rx,ry){
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var agents=[
      {name:'Owner',x:0,y:-55,z:0,col:'#e9a23b',r:14,type:'owner'},
      {name:'GC',x:0,y:-20,z:0,col:'#4ea0ff',r:12,type:'gc'},
      {name:'Steel',x:-55,y:15,z:-15,col:'#e0556b',r:9,type:'sub',disrupted:true},
      {name:'HVAC',x:-20,y:15,z:20,col:'#e2b13c',r:9,type:'sub',disrupted:true},
      {name:'Elec',x:20,y:15,z:-20,col:'#f0c040',r:9,type:'sub'},
      {name:'Concrete',x:55,y:15,z:15,col:'#3fcaa6',r:9,type:'sub'},
      {name:'Steel Mill',x:-60,y:50,z:-20,col:'#e0556b55',r:7,type:'supplier'},
      {name:'HVAC Mfg',x:-15,y:50,z:25,col:'#e2b13c55',r:7,type:'supplier'},
      {name:'Local',x:50,y:50,z:10,col:'#3fcaa6',r:7,type:'supplier'}
    ];
    var edges=[['Owner','GC',false],['GC','Steel',true],['GC','HVAC',true],['GC','Elec',false],['GC','Concrete',false],['Steel','Steel Mill',true],['HVAC','HVAC Mfg',true],['Concrete','Local',false]];
    var nodeMap={};agents.forEach(function(a){nodeMap[a.name]=a;});
    edges.forEach(function(e){
      var n1=nodeMap[e[0]],n2=nodeMap[e[1]];
      if(!n1||!n2)return;
      var p1=t(n1),p2=t(n2);if(!isFinite(p1.x))return;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      ctx.strokeStyle=e[2]?'#e0556b77':'rgba(78,160,255,0.3)';ctx.lineWidth=e[2]?2:1;
      if(e[2]){ctx.setLineDash([4,3]);}ctx.stroke();ctx.setLineDash([]);
    });
    agents.forEach(function(a){
      var p=t(a);if(!isFinite(p.x))return;
      var r2=Math.max(a.r*0.8,a.r*p.s);
      ctx.beginPath();ctx.arc(p.x,p.y,r2,0,Math.PI*2);ctx.fillStyle=a.col+'33';ctx.fill();
      ctx.strokeStyle=a.col;ctx.lineWidth=a.disrupted?2.5:1.5;ctx.stroke();
      if(a.disrupted){ctx.beginPath();ctx.arc(p.x,p.y,r2+5,0,Math.PI*2);ctx.strokeStyle='#e0556b44';ctx.lineWidth=2;ctx.stroke();}
      ctx.font='bold 7px SFMono-Regular,monospace';ctx.fillStyle=a.col;ctx.textAlign='center';ctx.fillText(a.name,p.x,p.y+3);ctx.textAlign='left';
    });
    axL(ctx,W/2,H-8,'Dashed red = disrupted supply chain path','#64748b','center');
  }

  // 5.8 Discrete Event Sim — 2D Gantt
  function render_58(ctx,W,H,m,rx,ry){
    ctx.clearRect(0,0,W,H);
    var PAD={l:72,r:14,t:20,b:28};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var events=[
      {name:'Concrete pour',start:0,dur:8,col:'#4ea0ff',delay:0},
      {name:'Steel erect',  start:6,dur:14,col:'#e2b13c',delay:2},
      {name:'MEP rough-in', start:18,dur:10,col:'#e0556b',delay:3},
      {name:'Drywall',      start:26,dur:8, col:'#f0c040',delay:1},
      {name:'Finishes',     start:32,dur:12,col:'#3fcaa6',delay:0},
      {name:'Commissioning',start:42,dur:6, col:'#9b6dff',delay:2}
    ];
    var maxT=50,bh=CH/events.length*0.58,gap=CH/events.length;
    // Grid
    [0,10,20,30,40,50].forEach(function(v){
      var x=PAD.l+v/maxT*CW;
      ctx.beginPath();ctx.moveTo(x,PAD.t);ctx.lineTo(x,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();
      axL(ctx,x,PAD.t+CH+12,'W'+v,'#64748b','center');
    });
    events.forEach(function(ev,i){
      var y=PAD.t+i*gap+gap/2-bh/2;
      // Planned bar
      var bx=PAD.l+ev.start/maxT*CW,bw=ev.dur/maxT*CW;
      ctx.fillStyle='rgba(100,116,139,0.25)';ctx.fillRect(bx,y,bw,bh);
      ctx.strokeStyle='rgba(100,116,139,0.4)';ctx.lineWidth=0.5;ctx.strokeRect(bx,y,bw,bh);
      // Actual bar (shifted by delay)
      var ax=PAD.l+(ev.start+ev.delay)/maxT*CW;
      ctx.fillStyle=ev.col;ctx.globalAlpha=0.85;ctx.fillRect(ax,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.25)';ctx.lineWidth=0.4;ctx.strokeRect(ax,y,bw,bh);
      // Label
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(ev.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      // Delay callout
      if(ev.delay>0){
        ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=ev.col;
        ctx.fillText('+'+ev.delay+'W',ax+bw+3,y+bh/2+3);
      }
    });
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='rgba(100,116,139,0.5)';ctx.fillText('▓ Planned',PAD.l,PAD.t-6);
    ctx.fillStyle='#e2b13c';ctx.fillText('▓ Actual (simulated)',PAD.l+60,PAD.t-6);
    axL(ctx,W/2,H-4,'Timeline (weeks)','#64748b','center');
  }

  /* CAT 6-12 RENDERERS (verbatim) */
  // ═══ CAT 6 — Signal Synthesis ════════════════════════════════
  function render_61(ctx,W,H,m,rx,ry){ // Conservative Dominance — state matrix
    ctx.clearRect(0,0,W,H);
    var signals=[{name:'EVM (Monte Carlo)',val:'Red',score:0.75},{name:'Schedule (CUSUM)',val:'Red',score:0.82},{name:'Doc Risk',val:'Amber',score:0.45},{name:'Schedule Sim',val:'Amber',score:0.60}];
    var states=['Green','Amber','Red'];
    var cols={Green:'#3fcaa6',Amber:'#e2b13c',Red:'#e0556b'};
    var PAD={l:130,r:20,t:28,b:36};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var rowH=CH/signals.length,colW=CW/3;
    // Header
    states.forEach(function(s,i){ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=cols[s];ctx.textAlign='center';ctx.fillText(s,PAD.l+i*colW+colW/2,PAD.t-8);ctx.textAlign='left';});
    signals.forEach(function(sig,i){
      var y=PAD.t+i*rowH;
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(sig.name,PAD.l-6,y+rowH/2+3);ctx.textAlign='left';
      states.forEach(function(s,j){
        var active=sig.val===s;
        var x=PAD.l+j*colW+4,bw=colW-8,bh=rowH-6;
        ctx.fillStyle=active?cols[s]+'33':'rgba(38,52,79,0.2)';ctx.fillRect(x,y+3,bw,bh);
        ctx.strokeStyle=active?cols[s]:'rgba(38,52,79,0.4)';ctx.lineWidth=active?1.5:0.4;ctx.strokeRect(x,y+3,bw,bh);
        if(active){ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=cols[s];ctx.textAlign='center';ctx.fillText('●',x+bw/2,y+rowH/2+3);ctx.textAlign='left';}
      });
    });
    // Result row
    var ry2=PAD.t+signals.length*rowH+6;
    ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText('→ RESULT',PAD.l-6,ry2+12);ctx.textAlign='left';
    var rx2=PAD.l+2*colW+4,rw=colW-8;
    ctx.fillStyle='#e0556b33';ctx.fillRect(rx2,ry2,rw,20);
    ctx.strokeStyle='#e0556b';ctx.lineWidth=2;ctx.strokeRect(rx2,ry2,rw,20);
    ctx.font='bold 10px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.textAlign='center';ctx.fillText('RED-REVIEW',rx2+rw/2,ry2+13);ctx.textAlign='left';
    aL(ctx,14,H-8,'Worst signal wins: 2× Red → Red-review','#64748b');
  }
  function render_62(ctx,W,H,m,rx,ry){ // Weighted Voting
    ctx.clearRect(0,0,W,H);
    var PAD={l:100,r:50,t:20,b:24};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var signals=[{name:'Monte Carlo',weight:0.35,score:0.78,col:'#e0556b'},{name:'CUSUM',weight:0.25,score:0.82,col:'#e0556b'},{name:'Doc Risk',weight:0.20,score:0.45,col:'#e2b13c'},{name:'Sched Sim',weight:0.20,score:0.60,col:'#e2b13c'}];
    var n=signals.length,rowH=CH/n,maxS=1.0;
    signals.forEach(function(s,i){
      var y=PAD.t+i*rowH+rowH*0.15;var bh=rowH*0.65;
      // Weight bar (thin, left)
      var ww=s.weight*60;
      ctx.fillStyle='rgba(100,116,139,0.3)';ctx.fillRect(PAD.l-66,y,ww,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='right';ctx.fillText((s.weight*100).toFixed(0)+'%',PAD.l-70,y+bh/2+3);ctx.textAlign='left';
      // Score bar (main)
      var bw=s.score/maxS*CW;
      ctx.fillStyle=s.col;ctx.globalAlpha=0.85;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(s.name,PAD.l-68,y+bh/2+3);ctx.textAlign='left';
      ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=s.col;ctx.fillText(s.score.toFixed(2),PAD.l+bw+4,y+bh/2+3);
    });
    // Weighted result
    var result=signals.reduce(function(sum,s){return sum+s.weight*s.score;},0);
    var ry2=PAD.t+n*rowH+6;
    aL(ctx,PAD.l,ry2+12,'Weighted score: ','#64748b');
    ctx.font='bold 11px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText(result.toFixed(3),PAD.l+90,ry2+12);
    pill(ctx,PAD.l+CW*0.7,ry2+12,'→ Red-review','#e0556b');
    [0.25,0.5,0.75,1.0].forEach(function(v){aL(ctx,PAD.l+v*CW,PAD.t+CH+12,v.toFixed(2),'#64748b','center');});
    aL(ctx,W/2,H-4,'Signal score (0–1)','#64748b','center');
  }
  function render_63(ctx,W,H,m,rx,ry){ // Majority Rules — donut
    ctx.clearRect(0,0,W,H);
    var cx=W/2,cy=H/2+5,R=70,inner=42;
    var votes=[{state:'Red',count:2,col:'#e0556b'},{state:'Amber',count:2,col:'#e2b13c'},{state:'Green',count:0,col:'#3fcaa6'}];
    var total=votes.reduce(function(s,v){return s+v.count;},0);
    var startA=-Math.PI/2;
    votes.forEach(function(v){
      if(!v.count)return;
      var sweep=(v.count/total)*Math.PI*2;
      ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,R,startA,startA+sweep);ctx.closePath();
      ctx.fillStyle=v.col+'cc';ctx.fill();ctx.strokeStyle='rgba(10,15,28,0.5)';ctx.lineWidth=1.5;ctx.stroke();
      // Inner cutout
      ctx.beginPath();ctx.arc(cx,cy,inner,0,Math.PI*2);ctx.fillStyle='var(--panel,#0f1729)';ctx.fill();
      // Label
      var midA=startA+sweep/2;
      var lx=cx+(R+18)*Math.cos(midA),ly=cy+(R+18)*Math.sin(midA);
      ctx.font='bold 9px SFMono-Regular,monospace';ctx.fillStyle=v.col;ctx.textAlign='center';
      ctx.fillText(v.state,lx,ly);ctx.fillText(v.count+' of '+total,lx,ly+11);ctx.textAlign='left';
      startA+=sweep;
    });
    ctx.textAlign='center';ctx.font='bold 11px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('TIE',cx,cy);
    ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('Red wins tie',cx,cy+13);ctx.textAlign='left';
    aL(ctx,14,H-8,'Tie-break rule: conservative dominance applies','#64748b');
  }
  function render_64(ctx,W,H,m,rx,ry){ // Worst-N-of-M scatter
    ctx.clearRect(0,0,W,H);
    var PAD={l:44,r:20,t:20,b:28};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var signals=[
      {name:'MC EAC',severity:0.78,confidence:0.92,state:'Red'},{name:'CUSUM',severity:0.82,confidence:0.88,state:'Red'},
      {name:'Doc Risk',severity:0.45,confidence:0.75,state:'Amber'},{name:'Sched Sim',severity:0.60,confidence:0.82,state:'Amber'},
      {name:'PERT',severity:0.55,confidence:0.70,state:'Amber'},{name:'LOB',severity:0.38,confidence:0.65,state:'Yellow'}
    ];
    // Grid
    [0.25,0.5,0.75].forEach(function(v){
      var x=PAD.l+v*CW,y=PAD.t+CH-v*CH;
      ctx.beginPath();ctx.moveTo(PAD.l,y);ctx.lineTo(PAD.l+CW,y);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();
      ctx.beginPath();ctx.moveTo(x,PAD.t);ctx.lineTo(x,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();
    });
    // Threshold line — worst 2 of 6 trigger Red
    var thresh=0.70;
    ctx.beginPath();ctx.moveTo(PAD.l+thresh*CW,PAD.t);ctx.lineTo(PAD.l+thresh*CW,PAD.t+CH);
    ctx.strokeStyle='#e0556b55';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([]);
    aL(ctx,PAD.l+thresh*CW+3,PAD.t+10,'Trigger\nthreshold','#e0556b');
    // Signals
    signals.forEach(function(s){
      var x=PAD.l+s.severity*CW,y=PAD.t+CH-(s.confidence)*CH;
      var col=SC[s.state];
      ctx.beginPath();ctx.arc(x,y,7,0,Math.PI*2);ctx.fillStyle=col+'cc';ctx.fill();ctx.strokeStyle=col;ctx.lineWidth=1.5;ctx.stroke();
      aL(ctx,x+10,y+3,s.name,'#9fb0cc');
    });
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.lineTo(PAD.l+CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
    [0,0.5,1].forEach(function(v){aL(ctx,PAD.l-4,PAD.t+CH-v*CH+3,(v).toFixed(1),'#64748b','right');aL(ctx,PAD.l+v*CW,PAD.t+CH+12,(v).toFixed(1),'#64748b','center');});
    aL(ctx,W/2,H-4,'Signal severity →','#64748b','center');
    ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);aL(ctx,0,0,'Confidence','#64748b','center');ctx.restore();
  }

  // ═══ CAT 7 — Evidence Combination (grouped) ═══════════════════
  function render_71(ctx,W,H,m,rx,ry){ // DST — arc rings belief masses
    var cx=W/2,cy=H/2+8;
    function t(p){return {x:cx+p.x, y:cy+p.z, s:1};}  // flat 2D donut (rings read top-down, not tilted)
    ctx.clearRect(0,0,W,H);
    var masses=[{label:'Belief: Red',val:0.52,col:'#e0556b',R:72,lw:14},{label:'Belief: Amber',val:0.28,col:'#e2b13c',R:52,lw:14},{label:'Belief: Green',val:0.08,col:'#3fcaa6',R:32,lw:14},{label:'Conflict mass',val:0.12,col:'#64748b',R:16,lw:8}];
    var startA=-Math.PI/2;
    masses.forEach(function(m){
      var steps=64,bg=[];
      for(var i=0;i<=steps;i++){var a=startA+(i/steps)*Math.PI*2;bg.push(t({x:m.R*Math.cos(a),y:0,z:m.R*Math.sin(a)}));}
      ctx.beginPath();bg.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});ctx.strokeStyle='rgba(38,52,79,0.5)';ctx.lineWidth=m.lw;ctx.stroke();
      var arc=bg.slice(0,Math.round(steps*m.val)+1);
      if(arc.length>1){ctx.beginPath();arc.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});ctx.strokeStyle=m.col;ctx.lineWidth=m.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';}
      var tipA=startA+m.val*Math.PI*2;
      var tp=t({x:m.R*Math.cos(tipA),y:0,z:m.R*Math.sin(tipA)});
      var cp=t({x:(m.R+26)*Math.cos(tipA),y:-4,z:(m.R+26)*Math.sin(tipA)});
      if(isFinite(tp.x)&&isFinite(cp.x)){
        ctx.beginPath();ctx.moveTo(tp.x,tp.y);ctx.lineTo(cp.x,cp.y);ctx.strokeStyle=m.col+'77';ctx.lineWidth=1;ctx.stroke();
        pill(ctx,cp.x,cp.y,m.label+' '+(m.val*100).toFixed(0)+'%',m.col);
      }
    });
    ctx.textAlign='center';ctx.font='bold 10px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('Red 0.52',cx,cy);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('Dempster-Shafer',cx,cy+13);ctx.textAlign='left';
  }
  function render_72_78(ctx,W,H,m,rx,ry){ // Modules 7.2–7.8 — comparison panel
    ctx.clearRect(0,0,W,H);
    var PAD={l:110,r:20,t:20,b:16};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var methods=[
      {name:'7.2 Rough Sets',result:'Definite Red',conf:0.82,col:'#e0556b',note:'Clear boundary'},
      {name:'7.3 Neutrosophic',result:'Red (I=0.18)',conf:0.74,col:'#e0556b',note:'Low indeterminacy'},
      {name:'7.4 Interval Fuzzy',result:'[0.48,0.72]',conf:0.68,col:'#e2b13c',note:'Wide interval'},
      {name:'7.5 Z-numbers',result:'Red r=0.83',conf:0.83,col:'#e0556b',note:'High reliability'},
      {name:'7.6 PLTS',result:'P(Red)=0.58',conf:0.58,col:'#e2b13c',note:'Probabilistic'},
      {name:'7.7 Plithogenic',result:'Contr 0.22',conf:0.71,col:'#e0556b',note:'Low contradiction'},
      {name:'7.8 BRB',result:'Red 0.59',conf:0.76,col:'#e0556b',note:'Rule-based'}
    ];
    var n=methods.length,rowH=CH/n;
    methods.forEach(function(m,i){
      var y=PAD.t+i*rowH+rowH*0.1,bh=rowH*0.75;
      var bw=m.conf*CW;
      ctx.fillStyle=m.col;ctx.globalAlpha=0.75;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(m.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=m.col;ctx.fillText(m.result,PAD.l+bw+4,y+bh/2+3);
    });
    [0.25,0.5,0.75,1.0].forEach(function(v){ctx.beginPath();ctx.moveTo(PAD.l+v*CW,PAD.t);ctx.lineTo(PAD.l+v*CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();aL(ctx,PAD.l+v*CW,PAD.t+CH+12,v.toFixed(2),'#64748b','center');});
    aL(ctx,W/2,H-4,'Confidence score','#64748b','center');
  }
  function render_79_720(ctx,W,H,m,rx,ry){ // Modules 7.9–7.20 — comparison panel
    ctx.clearRect(0,0,W,H);
    var PAD={l:120,r:20,t:20,b:16};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var methods=[
      {name:'7.9 Quantum',  result:'Constructive',conf:0.72,col:'#e0556b'},{name:'7.10 Pythagorean',result:'Red 0.69',conf:0.69,col:'#e0556b'},
      {name:'7.11 Picture', result:'Red 0.52',conf:0.52,col:'#e2b13c'},{name:'7.12 Hesitant',   result:'Low var',conf:0.65,col:'#e0556b'},
      {name:'7.13 Type-2',  result:'Red 0.71',conf:0.71,col:'#e0556b'},{name:'7.14 Max Entropy',result:'H=1.42',conf:0.68,col:'#e0556b'},
      {name:'7.15 Possibility',result:'Π(R)=0.89',conf:0.89,col:'#e0556b'},{name:'7.16 Spherical',result:'(0.61,0.22)',conf:0.61,col:'#e2b13c'},
      {name:'7.17 Fermatean',result:'0.73',conf:0.73,col:'#e0556b'},{name:'7.18 MARCOS',    result:'1.18',conf:0.78,col:'#e0556b'},
      {name:'7.19 TOPSIS',  result:'0.68',conf:0.68,col:'#e0556b'},{name:'7.20 Hypersoft', result:'Red',conf:0.75,col:'#e0556b'}
    ];
    var n=methods.length,rowH=CH/n;
    methods.forEach(function(m,i){
      var y=PAD.t+i*rowH+rowH*0.05,bh=rowH*0.82;
      var bw=m.conf*CW;
      ctx.fillStyle=m.col;ctx.globalAlpha=0.7;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(m.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=m.col;ctx.fillText(m.result,PAD.l+bw+4,y+bh/2+3);
    });
    [0.5,0.75,1.0].forEach(function(v){ctx.beginPath();ctx.moveTo(PAD.l+v*CW,PAD.t);ctx.lineTo(PAD.l+v*CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();aL(ctx,PAD.l+v*CW,PAD.t+CH+12,v.toFixed(2),'#64748b','center');});
    aL(ctx,W/2,H-4,'Confidence score  ·  all methods agree: Red','#64748b','center');
  }

  // ═══ CAT 8 — ML & AI ════════════════════════════════════════
  function render_81(ctx,W,H,m,rx,ry){ // Isolation Forest — 3D scatter
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    // Projects as dots, anomaly score = Z height
    var projects=[];
    for(var i=0;i<30;i++){
      var x=(Math.random()-0.5)*110,z=(Math.random()-0.5)*80;
      var score=Math.random()*0.4+0.2;
      projects.push({x:x,y:-score*60+20,z:z,score:score,anomaly:false});
    }
    // Project 06 is the anomaly
    projects.push({x:25,y:-0.74*60+20,z:20,score:0.74,anomaly:true});
    // Floor grid
    for(var g=-5;g<=5;g++){
      var p1=T({x:g*11,y:20,z:-45},rx,ry,fov,cx,cy),p2=T({x:g*11,y:20,z:45},rx,ry,fov,cx,cy);
      if(!isFinite(p1.x))return;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();
    }
    // Threshold plane
    var threshY=-0.60*60+20;
    [[{x:-55,z:-45},{x:55,z:-45}],[{x:55,z:-45},{x:55,z:45}],[{x:55,z:45},{x:-55,z:45}],[{x:-55,z:45},{x:-55,z:-45}]].forEach(function(edge){
      var p1=T({x:edge[0].x,y:threshY,z:edge[0].z},rx,ry,fov,cx,cy),p2=T({x:edge[1].x,y:threshY,z:edge[1].z},rx,ry,fov,cx,cy);
      if(!isFinite(p1.x))return;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e0556b55';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    });
    // Sort and draw dots
    projects.map(function(pr){var pp=T(pr,rx,ry,fov,cx,cy);return{pr:pr,pp:pp,pz:rX(rY(pr,ry),rx).z};}).sort(function(a,b){return a.pz-b.pz;}).forEach(function(s){
      if(!isFinite(s.pp.x))return;
      var col=s.pr.anomaly?'#e0556b':s.pr.score>0.6?'#e2b13c':'#4ea0ff';
      var r=s.pr.anomaly?7:Math.max(2,3.5*s.pp.s);
      ctx.beginPath();ctx.arc(s.pp.x,s.pp.y,r,0,Math.PI*2);ctx.fillStyle=col;ctx.globalAlpha=s.pr.anomaly?1:0.6;ctx.fill();ctx.globalAlpha=1;
      if(s.pr.anomaly){ctx.beginPath();ctx.arc(s.pp.x,s.pp.y,r+4,0,Math.PI*2);ctx.strokeStyle='#e0556b';ctx.lineWidth=1.5;ctx.stroke();pill(ctx,s.pp.x,s.pp.y-18,'Anomaly 74%','#e0556b');}
    });
    aL(ctx,14,18,'Dot height = anomaly score · threshold plane at 0.60','#64748b');
  }
  function render_82(ctx,W,H,m,rx,ry){ // Portfolio Outlier — 2D scatter
    ctx.clearRect(0,0,W,H);
    var PAD={l:44,r:20,t:20,b:28};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var projects=[
      {id:'01',cpi:1.02,spi:1.01,col:'#3fcaa6'},{id:'02',cpi:0.98,spi:0.97,col:'#3fcaa6'},
      {id:'03',cpi:0.96,spi:0.98,col:'#3fcaa6'},{id:'04',cpi:0.94,spi:0.95,col:'#e2b13c'},
      {id:'05',cpi:0.92,spi:0.93,col:'#e2b13c'},{id:'06',cpi:0.929,spi:0.911,col:'#e0556b',outlier:true},
      {id:'07',cpi:0.97,spi:0.96,col:'#3fcaa6'},{id:'08',cpi:0.99,spi:1.00,col:'#3fcaa6'},
      {id:'09',cpi:0.95,spi:0.94,col:'#e2b13c'}
    ];
    var minC=0.88,maxC=1.05,minS=0.88,maxS=1.05;
    function px(c){return PAD.l+(c-minC)/(maxC-minC)*CW;}
    function py(s){return PAD.t+CH-(s-minS)/(maxS-minS)*CH;}
    // Grid
    [0.90,0.95,1.00].forEach(function(v){
      ctx.beginPath();ctx.moveTo(px(v),PAD.t);ctx.lineTo(px(v),PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=v===1.0?0.8:0.4;ctx.stroke();
      ctx.beginPath();ctx.moveTo(PAD.l,py(v));ctx.lineTo(PAD.l+CW,py(v));ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=v===1.0?0.8:0.4;ctx.stroke();
      aL(ctx,px(v),PAD.t+CH+12,v.toFixed(2),'#64748b','center');aL(ctx,PAD.l-4,py(v)+3,v.toFixed(2),'#64748b','right');
    });
    projects.forEach(function(pr){
      var x=px(pr.cpi),y=py(pr.spi),r=pr.outlier?8:5;
      ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=pr.col;ctx.globalAlpha=0.85;ctx.fill();ctx.globalAlpha=1;
      if(pr.outlier){ctx.beginPath();ctx.arc(x,y,r+5,0,Math.PI*2);ctx.strokeStyle='#e0556b';ctx.lineWidth=1.5;ctx.stroke();pill(ctx,x,y-20,'Proj 06\n12th pct','#e0556b');}
      else{aL(ctx,x+7,y+3,'P'+pr.id,'#64748b');}
    });
    ctx.beginPath();ctx.moveTo(PAD.l,PAD.t);ctx.lineTo(PAD.l,PAD.t+CH);ctx.lineTo(PAD.l+CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.6)';ctx.lineWidth=0.6;ctx.stroke();
    aL(ctx,W/2,H-4,'CPI →','#64748b','center');ctx.save();ctx.translate(12,PAD.t+CH/2);ctx.rotate(-Math.PI/2);aL(ctx,0,0,'SPI','#64748b','center');ctx.restore();
  }
  function render_83(ctx,W,H,m,rx,ry){ // Trajectory Classifier — 3D line + boundary
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var cpiHist=[1.01,0.98,0.96,0.94,0.93,0.929],n=cpiHist.length,xSpan=110;
    function yv(v){return 40-(v-0.88)/0.18*80;}
    // Classification boundary plane
    var boundY=yv(0.93);
    var corners=[T({x:-xSpan/2,y:boundY,z:-25},rx,ry,fov,cx,cy),T({x:xSpan/2,y:boundY,z:-25},rx,ry,fov,cx,cy),T({x:xSpan/2,y:boundY,z:25},rx,ry,fov,cx,cy),T({x:-xSpan/2,y:boundY,z:25},rx,ry,fov,cx,cy)];
    if(corners.every(function(p){return isFinite(p.x);})){
      ctx.beginPath();ctx.moveTo(corners[0].x,corners[0].y);corners.forEach(function(p){ctx.lineTo(p.x,p.y);});ctx.closePath();ctx.fillStyle='rgba(224,85,107,0.06)';ctx.fill();ctx.strokeStyle='#e0556b55';ctx.lineWidth=1;ctx.stroke();
      aL(ctx,corners[1].x+4,corners[1].y,'Alert boundary','#e0556b','left');
    }
    // Trajectory line
    for(var i=0;i<n-1;i++){
      var x1=(i/(n-1)-0.5)*xSpan,x2=((i+1)/(n-1)-0.5)*xSpan;
      var col=cpiHist[i+1]<0.93?'#e0556b':'#e2b13c';
      var p1=t({x:x1,y:yv(cpiHist[i]),z:0}),p2=t({x:x2,y:yv(cpiHist[i+1]),z:0});
      if(!isFinite(p1.x))continue;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
      ctx.beginPath();ctx.arc(p2.x,p2.y,3,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
      aL(ctx,t({x:x1,y:yv(0.88)+12,z:0}).x,'M'+(i+1),'#64748b');
    }
    var lp=t({x:((n-1)/(n-1)-0.5)*xSpan,y:yv(cpiHist[n-1]),z:0});
    if(isFinite(lp.x)){pill(ctx,lp.x,lp.y-16,'Declining','#e0556b');aL(ctx,lp.x,lp.y+3,'M'+n,'#64748b','center');}
    aL(ctx,14,18,'Trajectory class: DECLINING · boundary crossed M5','#64748b');
  }
  function render_84(ctx,W,H,m,rx,ry){ // Cross-project heatmap
    ctx.clearRect(0,0,W,H);
    var PAD={l:44,r:14,t:20,b:32};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var projects=['P01','P02','P03','P04','P05','P06','P07','P08','P09'];
    var metrics=['CPI','SPI','Risk','CO Freq','Float'];
    var data=[[0.9,0.85,0.7,0.6,0.8],[0.85,0.9,0.75,0.5,0.85],[0.8,0.85,0.8,0.55,0.75],[0.75,0.8,0.7,0.65,0.7],[0.7,0.75,0.65,0.7,0.65],[0.85,0.78,0.6,0.72,0.58],[0.9,0.88,0.8,0.45,0.9],[0.92,0.9,0.85,0.4,0.92],[0.88,0.85,0.75,0.6,0.8]];
    var cw=CW/metrics.length,rh=CH/projects.length;
    data.forEach(function(row,ri){
      row.forEach(function(val,ci){
        var x=PAD.l+ci*cw,y=PAD.t+ri*rh;
        var col=val<0.65?'#e0556b':val<0.80?'#e2b13c':'#3fcaa6';
        ctx.fillStyle=col;ctx.globalAlpha=val*0.9;ctx.fillRect(x+1,y+1,cw-2,rh-2);ctx.globalAlpha=1;
        if(ri===5&&ci<3){ctx.strokeStyle='#ffffff55';ctx.lineWidth=1.5;ctx.strokeRect(x+1,y+1,cw-2,rh-2);}
      });
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(projects[ri],PAD.l-3,PAD.t+ri*rh+rh/2+3);ctx.textAlign='left';
    });
    metrics.forEach(function(m,i){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='center';ctx.fillText(m,PAD.l+i*cw+cw/2,PAD.t+CH+12);ctx.textAlign='left';});
    aL(ctx,14,14,'P06 row highlighted — consistent underperformer','#64748b');
  }
  function render_85(ctx,W,H,m,rx,ry){ // Anomaly Score — arc rings
    var cx=W/2,cy=H/2+8;
    function t(p){return {x:cx+p.x, y:cy+p.z, s:1};}  // flat 2D donut (rings read top-down, not tilted)
    ctx.clearRect(0,0,W,H);
    var components=[{label:'Isolation Forest',score:0.74,R:72,lw:14,col:'#e0556b'},{label:'Portfolio outlier',score:0.82,R:52,lw:14,col:'#e0556b'},{label:'Trajectory',score:0.68,R:32,lw:12,col:'#e2b13c'},{label:'Cross-project',score:0.60,R:16,lw:10,col:'#e2b13c'}];
    var startA=-Math.PI/2;
    components.forEach(function(m){
      var steps=64,bg=[];
      for(var i=0;i<=steps;i++){var a=startA+(i/steps)*Math.PI*2;bg.push(t({x:m.R*Math.cos(a),y:0,z:m.R*Math.sin(a)}));}
      ctx.beginPath();bg.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});ctx.strokeStyle='rgba(38,52,79,0.55)';ctx.lineWidth=m.lw;ctx.stroke();
      var arc=bg.slice(0,Math.round(steps*m.score)+1);
      if(arc.length>1){ctx.beginPath();arc.forEach(function(p,i){i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});ctx.strokeStyle=m.col;ctx.lineWidth=m.lw;ctx.lineCap='round';ctx.stroke();ctx.lineCap='butt';}
      var tipA=startA+m.score*Math.PI*2,tp=t({x:m.R*Math.cos(tipA),y:0,z:m.R*Math.sin(tipA)}),cp=t({x:(m.R+26)*Math.cos(tipA),y:-4,z:(m.R+26)*Math.sin(tipA)});
      if(isFinite(tp.x)&&isFinite(cp.x)){ctx.beginPath();ctx.moveTo(tp.x,tp.y);ctx.lineTo(cp.x,cp.y);ctx.strokeStyle=m.col+'77';ctx.lineWidth=1;ctx.stroke();pill(ctx,cp.x,cp.y,m.label+' '+(m.score*100).toFixed(0)+'%',m.col);}
    });
    ctx.textAlign='center';ctx.font='bold 11px SFMono-Regular,monospace';ctx.fillStyle='#e0556b';ctx.fillText('68%',cx,cy);ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.fillText('composite anomaly',cx,cy+13);ctx.textAlign='left';
  }

  // ═══ CAT 9 — Governance ════════════════════════════════════
  function render_91(ctx,W,H,m,rx,ry){ // ABM — authority decision tree
    ctx.clearRect(0,0,W,H);
    var cx=W/2;
    var nodes=[
      {label:'Signal Input',x:cx,y:22,col:'#64748b',w:100},
      {label:'Synthesis\n(Cat 6)',x:cx,y:60,col:'#e9a23b',w:90},
      {label:'GREEN',x:cx-140,y:110,col:'#3fcaa6',w:70},
      {label:'AMBER',x:cx,y:110,col:'#e2b13c',w:70},
      {label:'RED-REVIEW',x:cx+140,y:110,col:'#e0556b',w:100},
      {label:'PM Monitor',x:cx-140,y:155,col:'#3fcaa6',w:90},
      {label:'PM + Controls\nWeekly review',x:cx,y:155,col:'#e2b13c',w:110},
      {label:'Program Director\n48hr escalation',x:cx+140,y:155,col:'#e0556b',w:120},
      {label:'Fairness\nGate',x:cx+140,y:200,col:'#9b6dff',w:80}
    ];
    var edges=[[0,1],[1,2],[1,3],[1,4],[2,5],[3,6],[4,7],[7,8]];
    edges.forEach(function(e){
      var n1=nodes[e[0]],n2=nodes[e[1]];
      ctx.beginPath();ctx.moveTo(n1.x,n1.y+10);ctx.lineTo(n2.x,n2.y-10);
      ctx.strokeStyle='rgba(100,116,139,0.4)';ctx.lineWidth=1;ctx.stroke();
      var ang=Math.atan2(n2.y-n1.y,n2.x-n1.x);
      var mx=n1.x+(n2.x-n1.x)*0.6,my=n1.y+(n2.y-n1.y)*0.6;
      ctx.save();ctx.translate(mx,my);ctx.rotate(ang);ctx.beginPath();ctx.moveTo(-4,-3);ctx.lineTo(4,0);ctx.lineTo(-4,3);ctx.fillStyle='rgba(100,116,139,0.5)';ctx.fill();ctx.restore();
    });
    nodes.forEach(function(n){
      var lines=n.label.split('\n'),bh=lines.length>1?28:18,bw=n.w;
      if(ctx.roundRect)ctx.roundRect(n.x-bw/2,n.y-bh/2,bw,bh,5);else ctx.rect(n.x-bw/2,n.y-bh/2,bw,bh);
      ctx.fillStyle=n.col+'22';ctx.fill();ctx.strokeStyle=n.col;ctx.lineWidth=1.5;ctx.stroke();
      ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=n.col;ctx.textAlign='center';
      lines.forEach(function(l,li){ctx.fillText(l,n.x,n.y-(lines.length-1)*5+li*10);});ctx.textAlign='left';
    });
  }
  function render_92_99(ctx,W,H,m,rx,ry){ // Governance modules 9.2–9.9 overview
    ctx.clearRect(0,0,W,H);
    var PAD={l:110,r:20,t:20,b:16};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var items=[
      {name:'9.2 FAR Threshold',val:0.92,status:'Red',note:'8.2% cost growth'},
      {name:'9.3 OMB A-11',val:1.0,status:'Green',note:'Reporting met'},
      {name:'9.4 EVM Reporting',val:1.0,status:'Green',note:'On schedule'},
      {name:'9.5 Contract Mod Freq',val:0.65,status:'Amber',note:'1 mod issued'},
      {name:'9.6 Quality Compliance',val:0.72,status:'Amber',note:'NCR rate rising'},
      {name:'9.7 Safety Performance',val:0.88,status:'Amber',note:'1 minor incident'},
      {name:'9.8 Environmental Comp',val:0.95,status:'Green',note:'All permits active'},
      {name:'9.9 Contractor Score',val:0.68,status:'Amber',note:'Composite 68%'}
    ];
    var n=items.length,rowH=CH/n;
    items.forEach(function(m,i){
      var y=PAD.t+i*rowH+rowH*0.1,bh=rowH*0.75,bw=m.val*CW;
      var col=SC[m.status];
      ctx.fillStyle=col;ctx.globalAlpha=0.8;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(m.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=col;ctx.fillText(m.note,PAD.l+bw+4,y+bh/2+3);
    });
    [0.5,1.0].forEach(function(v){ctx.beginPath();ctx.moveTo(PAD.l+v*CW,PAD.t);ctx.lineTo(PAD.l+v*CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();aL(ctx,PAD.l+v*CW,PAD.t+CH+12,v.toFixed(1),'#64748b','center');});
    aL(ctx,W/2,H-4,'Compliance score (0–1)','#64748b','center');
  }

  // ═══ CAT 10 — Data Integrity ═════════════════════════════════
  function render_101(ctx,W,H,m,rx,ry){ // Missing data heatmap
    ctx.clearRect(0,0,W,H);
    var PAD={l:64,r:14,t:20,b:32};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var docTypes=['Pay App','Field Rpt','OAC Mins','RFI Log','Schedule'];
    var fields=['BAC','EV','AC','PV','SPI','CPI','Float','Risk'];
    var present=[[1,1,1,1,1,1,0,0],[0,0,0,1,1,0,1,1],[0,1,0,0,1,0,0,1],[0,0,0,0,1,0,1,1],[0,0,0,1,1,0,1,0]];
    var cw=CW/fields.length,rh=CH/docTypes.length;
    present.forEach(function(row,ri){
      row.forEach(function(v,ci){
        var x=PAD.l+ci*cw+1,y=PAD.t+ri*rh+1,bw=cw-2,bh=rh-2;
        ctx.fillStyle=v?'#3fcaa666':'rgba(224,85,107,0.15)';ctx.fillRect(x,y,bw,bh);
        ctx.font='9px SFMono-Regular,monospace';ctx.fillStyle=v?'#3fcaa6':'#e0556b';ctx.textAlign='center';ctx.fillText(v?'✓':'✗',x+bw/2,y+bh/2+3);ctx.textAlign='left';
      });
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(docTypes[ri],PAD.l-3,PAD.t+ri*rh+rh/2+3);ctx.textAlign='left';
    });
    fields.forEach(function(f,i){ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#64748b';ctx.textAlign='center';ctx.save();ctx.translate(PAD.l+i*cw+cw/2,PAD.t+CH+14);ctx.rotate(-Math.PI/6);ctx.fillText(f,0,0);ctx.restore();ctx.textAlign='left';});
    pill(ctx,W*0.7,16,'73% completeness','#e2b13c');
  }
  function render_102_107(ctx,W,H,m,rx,ry){ // Data integrity 10.2–10.7
    ctx.clearRect(0,0,W,H);
    var PAD={l:120,r:20,t:20,b:16};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var items=[
      {name:'10.2 Timeliness',val:0.58,col:'#e2b13c',note:'12 days avg lag'},
      {name:'10.3 Src Reliability',val:0.81,col:'#3fcaa6',note:'Pay app = 0.85'},
      {name:'10.4 Audit Trail',val:1.00,col:'#3fcaa6',note:'100% logged'},
      {name:'10.5 Completeness',val:0.73,col:'#e2b13c',note:'27 fields missing'},
      {name:'10.6 Cross-doc Consistency',val:1.00,col:'#3fcaa6',note:'No conflicts'},
      {name:'10.7 Reporting Frequency',val:0.72,col:'#e2b13c',note:'9-day interval'}
    ];
    var n=items.length,rowH=CH/n;
    items.forEach(function(m,i){
      var y=PAD.t+i*rowH+rowH*0.1,bh=rowH*0.75,bw=m.val*CW;
      ctx.fillStyle=m.col;ctx.globalAlpha=0.8;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(m.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=m.col;ctx.fillText(m.note,PAD.l+bw+4,y+bh/2+3);
    });
    [0.5,0.75,1.0].forEach(function(v){ctx.beginPath();ctx.moveTo(PAD.l+v*CW,PAD.t);ctx.lineTo(PAD.l+v*CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();aL(ctx,PAD.l+v*CW,PAD.t+CH+12,v.toFixed(2),'#64748b','center');});
    aL(ctx,W/2,H-4,'Data quality score (0–1)','#64748b','center');
  }

  // ═══ CAT 11 — Decision Optimization ═════════════════════════
  function render_111(ctx,W,H,m,rx,ry){ // Multi-objective Pareto surface
    var cx=W/2,cy=H/2+5,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    // Pareto front as surface, dominated solutions as dots below
    var xSpan=100,ySpan=80;
    // Pareto front curve
    var pareto=[];
    for(var i=0;i<=20;i++){
      var cost=i/20,sched=1-Math.pow(cost,0.6);
      pareto.push({x:(cost-0.5)*xSpan,y:-sched*60+20,z:0});
    }
    // Dominated solutions
    var dominated=[];
    for(var i=0;i<20;i++){
      var c=Math.random(),s=Math.random()*(1-Math.pow(c,0.6))*0.8;
      dominated.push({x:(c-0.5)*xSpan,y:-s*60+20,z:(Math.random()-0.5)*40});
    }
    dominated.forEach(function(d){
      var pp=t(d);if(!isFinite(pp.x))return;
      ctx.beginPath();ctx.arc(pp.x,pp.y,3,0,Math.PI*2);ctx.fillStyle='rgba(100,116,139,0.4)';ctx.fill();
    });
    // Pareto front line
    var ppPts=pareto.map(function(p){return t(p);});
    ctx.beginPath();ppPts.forEach(function(p,i){if(!isFinite(p.x))return;i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
    ctx.strokeStyle='#4ea0ff';ctx.lineWidth=2.5;ctx.stroke();
    // Current solution dot
    var cur=t({x:0.2*xSpan-xSpan/2,y:-(1-Math.pow(0.7,0.6))*60+20,z:0});
    if(isFinite(cur.x)){ctx.beginPath();ctx.arc(cur.x,cur.y,6,0,Math.PI*2);ctx.fillStyle='#e0556b';ctx.fill();pill(ctx,cur.x,cur.y-16,'Current','#e0556b');}
    // Optimal solution
    var opt=t({x:0.5*xSpan-xSpan/2,y:-(1-Math.pow(0.5,0.6))*60+20,z:0});
    if(isFinite(opt.x)){ctx.beginPath();ctx.arc(opt.x,opt.y,6,0,Math.PI*2);ctx.fillStyle='#3fcaa6';ctx.fill();pill(ctx,opt.x,opt.y-16,'Optimal','#3fcaa6');}
    aL(ctx,14,H-8,'Blue = Pareto front · Grey = dominated · drag to rotate','#64748b');
  }
  function render_112_117(ctx,W,H,m,rx,ry){ // Decision optim 11.2–11.7
    ctx.clearRect(0,0,W,H);
    var PAD={l:130,r:20,t:20,b:16};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var items=[
      {name:'11.2 Linear Programming',val:0.78,col:'#e0556b',note:'CPI req 1.076'},
      {name:'11.3 Constraint Sat',val:0.50,col:'#e0556b',note:'2 of 4 violated'},
      {name:'11.4 What-If',val:0.65,col:'#e2b13c',note:'EAC range ±11.2%'},
      {name:'11.5 Decision Sensitivity',val:0.68,col:'#e2b13c',note:'68% sensitive'},
      {name:'11.6 Pareto Frontier',val:0.42,col:'#e0556b',note:'Dominated solution'},
      {name:'11.7 Regret Minimization',val:0.80,col:'#e0556b',note:'Escalate recommended'}
    ];
    var n=items.length,rowH=CH/n;
    items.forEach(function(m,i){
      var y=PAD.t+i*rowH+rowH*0.1,bh=rowH*0.75,bw=m.val*CW;
      ctx.fillStyle=m.col;ctx.globalAlpha=0.8;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(m.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=m.col;ctx.fillText(m.note,PAD.l+bw+4,y+bh/2+3);
    });
    [0.5,1.0].forEach(function(v){ctx.beginPath();ctx.moveTo(PAD.l+v*CW,PAD.t);ctx.lineTo(PAD.l+v*CW,PAD.t+CH);ctx.strokeStyle='rgba(38,52,79,0.3)';ctx.lineWidth=0.4;ctx.stroke();aL(ctx,PAD.l+v*CW,PAD.t+CH+12,v.toFixed(1),'#64748b','center');});
    aL(ctx,W/2,H-4,'Optimization score (0–1)','#64748b','center');
  }

  // ═══ CAT 12 — Systems Engineering (conditional) ══════════════
  function render_121(ctx,W,H,m,rx,ry){ // Interface Density network
    var cx=W/2,cy=H/2,fov=Math.min(W,H)*0.85;
    function t(p){return prj(rX(rY(p,ry),rx),fov,cx,cy);}
    ctx.clearRect(0,0,W,H);
    var systems=[{name:'HVAC',x:-50,y:-30,z:-20,col:'#4ea0ff'},{name:'Elec',x:50,y:-30,z:20,col:'#e2b13c'},{name:'Plumbing',x:-50,y:30,z:20,col:'#3fcaa6'},{name:'Struct',x:50,y:30,z:-20,col:'#9b6dff'},{name:'Controls',x:0,y:0,z:0,col:'#e9a23b'}];
    var ifaces=[[0,4,0.8],[1,4,0.7],[2,4,0.6],[3,4,0.5],[0,1,0.4],[1,3,0.3],[0,2,0.3],[2,3,0.4]];
    ifaces.forEach(function(e){
      var n1=systems[e[0]],n2=systems[e[1]];
      var p1=t(n1),p2=t(n2);if(!isFinite(p1.x))return;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
      var col=e[2]>0.6?'#e0556b':e[2]>0.4?'#e2b13c':'rgba(100,116,139,0.4)';
      ctx.strokeStyle=col;ctx.lineWidth=e[2]*3;ctx.stroke();
    });
    systems.forEach(function(s){
      var p=t(s);if(!isFinite(p.x))return;
      var r=Math.max(12,15*p.s);
      ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fillStyle=s.col+'22';ctx.fill();ctx.strokeStyle=s.col;ctx.lineWidth=1.8;ctx.stroke();
      ctx.font='bold 8px SFMono-Regular,monospace';ctx.fillStyle=s.col;ctx.textAlign='center';ctx.fillText(s.name,p.x,p.y+3);ctx.textAlign='left';
    });
    aL(ctx,14,H-8,'Line weight = interface density · conditional on ICD upload','#64748b');
  }
  function render_122_125(ctx,W,H,m,rx,ry){ // Cat 12 overview 12.2–12.5
    ctx.clearRect(0,0,W,H);
    var PAD={l:130,r:20,t:20,b:20};var CW=W-PAD.l-PAD.r,CH=H-PAD.t-PAD.b;
    var items=[
      {name:'12.2 Dependency Map',status:'Conditional',note:'Requires DSM upload',val:0},
      {name:'12.3 Requirements Trace',status:'Conditional',note:'Requires req matrix',val:0},
      {name:'12.4 Config Change Impact',status:'Amber',note:'CO impact 10%',val:0.55},
      {name:'12.5 Integration Complexity',status:'Conditional',note:'Requires ICD data',val:0}
    ];
    var n=items.length,rowH=CH/n;
    items.forEach(function(m,i){
      var y=PAD.t+i*rowH+rowH*0.12,bh=rowH*0.7;
      var col=m.status==='Amber'?'#e2b13c':'#64748b';
      var bw=m.val>0?m.val*CW:CW*0.15;
      ctx.fillStyle=col;ctx.globalAlpha=m.val>0?0.8:0.2;ctx.fillRect(PAD.l,y,bw,bh);ctx.globalAlpha=1;
      ctx.strokeStyle='rgba(10,15,28,0.2)';ctx.lineWidth=0.3;ctx.strokeRect(PAD.l,y,bw,bh);
      ctx.font='8px SFMono-Regular,monospace';ctx.fillStyle='#9fb0cc';ctx.textAlign='right';ctx.fillText(m.name,PAD.l-4,y+bh/2+3);ctx.textAlign='left';
      ctx.fillStyle=col;ctx.fillText(m.note,PAD.l+bw+4,y+bh/2+3);
    });
    aL(ctx,W/2,H-4,'Conditional modules — activate when interface docs uploaded','#64748b','center');
  }

  window.LinCharts3D = {
    rX: rX, rY: rY, proj: proj,
    pillDraw:          pillDraw,
    render_histogram3d: render_histogram3d,
    render_cusum3d:     render_cusum3d,
    render_risk3d:      render_risk3d,
    render_bayesian3d:  render_bayesian3d,
    render_kalman3d:    render_kalman3d,
    render_arima3d:     render_arima3d,
    render_es3d:        render_es3d,
    render_tcpi3d:      render_tcpi3d,
    render_vac3d:       render_vac3d,
    render_ber3d:       render_ber3d,
    render_rtm3d:       render_rtm3d,
    render_ice3d:       render_ice3d,
    render_pert3d:      render_pert3d,
    render_lob2d:       render_lob2d,
    render_ccpm3d:      render_ccpm3d,
    render_sci3d:       render_sci3d,
    render_float3d:     render_float3d,
    render_scurve3d:    render_scurve3d,
    render_mta3d:       render_mta3d,
    render_lookahead3d: render_lookahead3d,
    render_resource3d:  render_resource3d,
    render_schedp80:    render_schedp80,
    render_cpisched3d:  render_cpisched3d,
    wireChart3d:        wireChart3d,
    render_rcf3d:         render_rcf3d,
    render_dsm3d:         render_dsm3d,
    render_contingency3d: render_contingency3d,
    render_labor3d:       render_labor3d,
    render_material3d:    render_material3d,
    render_overhead3d:    render_overhead3d,
    render_costrisk3d:    render_costrisk3d,
    render_analogous3d:   render_analogous3d,
    render_parametric3d:  render_parametric3d,
    render_inflation3d:   render_inflation3d,
    render_41: render_41,
    render_42: render_42,
    render_43: render_43,
    render_44: render_44,
    render_45: render_45,
    render_46: render_46,
    render_47: render_47,
    render_48: render_48,
    render_49: render_49,
    render_410: render_410,
    render_51: render_51,
    render_52: render_52,
    render_53: render_53,
    render_54: render_54,
    render_55: render_55,
    render_56: render_56,
    render_57: render_57,
    render_58: render_58,
    render_61: render_61,
    render_62: render_62,
    render_63: render_63,
    render_64: render_64,
    render_71: render_71,
    render_72_78: render_72_78,
    render_79_720: render_79_720,
    render_81: render_81,
    render_82: render_82,
    render_83: render_83,
    render_84: render_84,
    render_85: render_85,
    render_91: render_91,
    render_92_99: render_92_99,
    render_101: render_101,
    render_102_107: render_102_107,
    render_111: render_111,
    render_112_117: render_112_117,
    render_121: render_121,
    render_122_125: render_122_125
  };
})();
