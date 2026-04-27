let VOC_DATA = {"brands":[],"data":{}};
let currentBrand=null,currentCat=null,currentItem=null;
let reviewPage=0;
const PAGE_SIZE=5;

function b64ToBytes(b64){const bin=atob(b64);const b=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)b[i]=bin.charCodeAt(i);return b;}

async function unlock(){
  const pw=document.getElementById('pwInput').value;
  const errEl=document.getElementById('pwError');
  const loadEl=document.getElementById('pwLoading');
  const btn=document.getElementById('unlockBtn');
  errEl.textContent='';
  if(!pw){errEl.textContent='비밀번호를 입력하세요.';return;}
  btn.disabled=true;
  loadEl.textContent='확인 중...';
  try{
    const enc=new TextEncoder();
    const salt=b64ToBytes(VOC_ENCRYPTED.salt);
    const iv=b64ToBytes(VOC_ENCRYPTED.iv);
    const ct=b64ToBytes(VOC_ENCRYPTED.ct);
    const keyMat=await crypto.subtle.importKey('raw',enc.encode(pw),'PBKDF2',false,['deriveKey']);
    const key=await crypto.subtle.deriveKey(
      {name:'PBKDF2',salt,iterations:100000,hash:'SHA-256'},
      keyMat,{name:'AES-GCM',length:256},false,['decrypt']
    );
    const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv},key,ct);
    VOC_DATA=JSON.parse(new TextDecoder().decode(plain));
    document.getElementById('loginOverlay').style.display='none';
    document.getElementById('app').style.display='block';
    init();
  }catch(e){
    errEl.textContent='비밀번호가 올바르지 않습니다.';
  }finally{
    btn.disabled=false;
    loadEl.textContent='';
  }
}

function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fmt(n){return Number(n).toLocaleString('ko-KR');}
function renderTabs(){
  document.getElementById('brandTabs').innerHTML=(VOC_DATA.brands||[])
    .map(b=>`<div class="brand-tab${b===currentBrand?' active':''}" onclick="selectBrand('${esc(b)}')">${esc(b)}</div>`).join('');
}
function renderMain(){
  const el=document.getElementById('mainContent');
  const d=VOC_DATA.data?.[currentBrand];
  if(!d){el.innerHTML='';return;}
  const allItems=(d.아이템목록||[]).slice().sort((a,b)=>(d.아이템별?.[b]?.총리뷰수??0)-(d.아이템별?.[a]?.총리뷰수??0));
  if(!currentItem&&allItems.length)currentItem=allItems[0];
  const itemCats=(d.아이템별?.[currentItem]?.피드백카테고리별||[]);
  if(!itemCats.some(c=>c.카테고리명===currentCat))
    currentCat=itemCats.length?itemCats[0].카테고리명:null;
  el.innerHTML=summaryBarHTML(d)+itemTabsHTML(d,allItems)+panelsHTML(d,itemCats);
}
function summaryBarHTML(d){
  return `<div class="summary-bar">
    <div class="stat-chip">총 리뷰 <strong>${fmt(d.총리뷰수)}건</strong></div>
    <div class="stat-chip">분석 대상 <strong>${fmt(d.분석대상리뷰수)}건</strong></div>
    <div class="stat-chip" style="color:#aaa;font-size:.76rem">광고성·중복 제외 기준</div>
  </div>`;
}
function itemTabsHTML(d,items){
  return `<div class="item-tabs-wrap"><div class="item-tabs">`+items.map(nm=>{
    const codes=(d.아이템별?.[nm]?.아이템코드||[]).join('·');
    return `<div class="item-tab${nm===currentItem?' active':''}" onclick="selectItem('${esc(nm)}')">
      <span class="item-tab-name">${esc(nm)}</span>
      ${codes?`<span class="item-tab-codes">(${esc(codes)})</span>`:''}
    </div>`;
  }).join('')+`</div></div>`;
}
function panelsHTML(d,itemCats){
  return `<div class="panels">${catPanelHTML(itemCats)}${reviewPanelHTML(d)}</div>`;
}
function catPanelHTML(itemCats){
  const rows=itemCats.map(cat=>{
    const neg=cat.부정비중??0;
    const col=neg>=70?'#e53935':neg>=50?'#fb8c00':'#43a047';
    return `<div class="cat-row${cat.카테고리명===currentCat?' active':''}" onclick="selectCat('${esc(cat.카테고리명)}')">
      <div class="cat-row-top">
        <span class="cat-row-name">${esc(cat.카테고리명)}</span>
        <span class="cat-row-cnt">${fmt(cat.리뷰수)}건</span>
      </div>
      <div class="sent-bar"><div class="sent-bar-inner" style="width:${neg}%;background:${col}"></div></div>
      <div class="sent-labels"><span class="lbl-neg">부정 ${neg}%</span><span class="lbl-pos">긍정 ${cat.긍정비중??0}%</span></div>
    </div>`;
  }).join('');
  return `<div class="cat-panel"><div class="cat-panel-title">피드백 카테고리</div><div class="cat-panel-list">${rows||'<p class="no-data">카테고리 없음</p>'}</div></div>`;
}
function reviewPanelHTML(d){
  const id=d.아이템별?.[currentItem];
  const cat=(id?.피드백카테고리별||[]).find(c=>c.카테고리명===currentCat);
  if(!cat)return`<div class="review-panel"><p class="no-data">카테고리를 선택하세요</p></div>`;

  const negAll=cat.대표부정리뷰||[];
  const posAll=cat.대표긍정리뷰||[];
  const totalPages=Math.max(1,Math.ceil(Math.max(negAll.length,posAll.length)/PAGE_SIZE));
  const page=reviewPage%totalPages;
  const s=page*PAGE_SIZE, e=s+PAGE_SIZE;

  const nc=negAll.slice(s,e).map(r=>rcHTML(r,'neg')).join('');
  const pc=posAll.slice(s,e).map(r=>rcHTML(r,'pos')).join('');

  return `<div class="review-panel">
    <div class="review-panel-title">
      ${esc(currentItem)} &nbsp;›&nbsp; ${esc(currentCat)}
      <span class="badge badge-neg">부정 ${cat.부정비중}%</span>
      <span class="badge badge-pos">긍정 ${cat.긍정비중}%</span>
      <span style="margin-left:auto;display:flex;align-items:center;gap:10px">
        <span style="font-size:.76rem;color:#bbb;font-weight:400">${fmt(cat.리뷰수)}건 분석</span>
        <button onclick="nextReviewPage()" style="display:flex;align-items:center;gap:5px;padding:5px 12px;background:#f0f2f7;border:1.5px solid #dde;border-radius:20px;font-size:.78rem;font-weight:700;color:#3f51b5;cursor:pointer;transition:background .15s" onmouseover="this.style.background='#e8eaf6'" onmouseout="this.style.background='#f0f2f7'">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3"/></svg>
          ${page+1}/${totalPages}
        </button>
      </span>
    </div>
    <div class="section-label">부정 대표 리뷰</div>
    ${nc||'<p class="no-data" style="text-align:left;padding:12px 0">해당 리뷰 없음</p>'}
    <hr class="divider">
    <div class="section-label">긍정 대표 리뷰</div>
    ${pc||'<p class="no-data" style="text-align:left;padding:12px 0">해당 리뷰 없음</p>'}
    ${shopLinkQualityHTML(cat)}
  </div>`;
}
function shopLinkQualityHTML(cat){
  if(cat.카테고리명!=='상품품질')return'';
  const reviews=cat.샵링크품질리뷰||[];
  if(!reviews.length)return'';
  const cards=reviews.map(r=>{
    const tags=[
      r.상품명?`<span class="tag product">${esc(r.상품명)}</span>`:'',
      r.시즌?`<span class="tag season">${esc(r.시즌)}</span>`:'',
    ].filter(Boolean).join('');
    return`<div class="review-card shoplink-q"><div class="review-text">${esc(r.텍스트)}</div><div class="review-meta">${tags}</div></div>`;
  }).join('');
  return`<hr class="divider"><div class="section-label shoplink-label">샵링크 품질 이슈 리뷰</div><div class="shoplink-note">교환·반품 채널(shoplink) 중 품질 관련 주요 리뷰</div>${cards}`;
}
function rcHTML(r,t){
  const tags=[
    r.상품명?`<span class="tag product">${esc(r.상품명)}</span>`:'',
    r.채널?`<span class="tag channel">${esc(r.채널)}</span>`:'',
    r.시즌?`<span class="tag season">${esc(r.시즌)}</span>`:''
  ].filter(Boolean).join('');
  return `<div class="review-card ${t}"><div class="review-text">${esc(r.텍스트)}</div><div class="review-meta">${tags}</div></div>`;
}
function nextReviewPage(){reviewPage++;renderMain();}
function selectBrand(b){currentBrand=b;currentCat=null;currentItem=null;reviewPage=0;renderTabs();renderMain();}
function selectCat(c){currentCat=c;reviewPage=0;renderMain();}
function selectItem(i){
  currentItem=i;reviewPage=0;
  const d=VOC_DATA.data?.[currentBrand];
  const itemCats=(d?.아이템별?.[i]?.피드백카테고리별||[]);
  if(!itemCats.some(c=>c.카테고리명===currentCat))
    currentCat=itemCats.length?itemCats[0].카테고리명:null;
  renderMain();
}
function init(){if(!VOC_DATA.brands?.length)return;currentBrand=VOC_DATA.brands[0];renderTabs();renderMain();}
