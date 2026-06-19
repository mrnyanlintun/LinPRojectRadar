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
    var cx=W/2,cy=H/2+8,fov=Math.min(W,H)*0.9;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
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
    var cx=W/2,cy=H/2+8,fov=Math.min(W,H)*0.9;
    function t(pt){return proj(rX(rY(pt,ry),rx),fov,cx,cy);}
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

  /* ---------- canvas wiring helper ---------- */
  function wireChart3d(canvas, renderFn, moduleData, opts) {
    var options = opts || {};
    var isDraggable = options.draggable !== false;
    var dpr = window.devicePixelRatio || 1;
    var wrap = canvas.parentElement;
    function resize() {
      var w = (wrap && wrap.clientWidth) || 500;
      canvas.width = w * dpr;
      canvas.height = 200 * dpr;
      canvas.style.width = w + 'px';
      canvas.style.height = '200px';
    }
    resize();
    var ctx = canvas.getContext('2d');
    var rx = options.rx !== undefined ? options.rx : 0.28;
    var ry = options.ry !== undefined ? options.ry : -0.35;
    function redraw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save(); ctx.scale(dpr, dpr);
      renderFn(ctx, canvas.width / dpr, canvas.height / dpr, moduleData, rx, ry);
      ctx.restore();
    }
    redraw();
    if (isDraggable) {
      var dragging = false, lastX = 0, lastY = 0;
      canvas.style.cursor = 'grab';
      canvas.addEventListener('mousedown', function(e) {
        dragging = true; lastX = e.clientX; lastY = e.clientY;
        canvas.style.cursor = 'grabbing';
      });
      window.addEventListener('mouseup', function() {
        dragging = false; canvas.style.cursor = 'grab';
      });
      canvas.addEventListener('mousemove', function(e) {
        if (!dragging) return;
        ry += (e.clientX - lastX) * 0.005;
        rx += (e.clientY - lastY) * 0.005;
        lastX = e.clientX; lastY = e.clientY;
        redraw();
      });
    }
    window.addEventListener('resize', function() { resize(); redraw(); });
  }

  window.LinCharts3D = {
    rX: rX, rY: rY, proj: proj,
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
    wireChart3d:        wireChart3d
  };
})();
