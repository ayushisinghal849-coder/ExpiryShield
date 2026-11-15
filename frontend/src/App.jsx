import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowRight, ArrowUpRight, Bell, Boxes, CheckCircle2,
  ChevronDown, CircleHelp, Clock3, CloudUpload, FileSpreadsheet, LayoutDashboard,
  Lightbulb, MapPin, MoreHorizontal, Package, RefreshCw, Search, Settings,
  ShieldCheck, ShoppingBasket, Sparkles, Store, Truck, X, Download, Play, RotateCcw
} from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart } from "recharts";
import {
  loadDashboard, loadRecommendations, runAnalysis, loadAnalysis,
  approveRecommendation, rejectRecommendation, completeRecommendation,
  uploadInventory, loadDemoScenarios, applyDemoScenario
} from "./api";

const money = v => new Intl.NumberFormat("en-IN", {style:"currency",currency:"INR",maximumFractionDigits:0}).format(Number(v||0));
const titleCase = s => String(s||"").toLowerCase().replace(/\b\w/g, c=>c.toUpperCase());

function App(){
  const [active,setActive]=useState("Dashboard");
  const [analytics,setAnalytics]=useState(null);
  const [inventory,setInventory]=useState([]);
  const [recommendations,setRecommendations]=useState([]);
  const [stores,setStores]=useState([]);
  const [analysis,setAnalysis]=useState(null);
  const [scenarios,setScenarios]=useState([]);
  const [scenarioId,setScenarioId]=useState("transfer-opportunity");
  const [selectedStore,setSelectedStore]=useState("all");
  const [search,setSearch]=useState("");
  const [riskFilter,setRiskFilter]=useState("All risk");
  const [connected,setConnected]=useState(false);
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState("");
  const [showUpload,setShowUpload]=useState(false);

  const refresh=async()=>{
    setBusy(true);
    try{
      const d=await loadDashboard();
      setAnalytics(d.analytics);setInventory(d.inventory);setStores(d.stores);setConnected(true);
      const recs=await loadRecommendations();setRecommendations(recs);
      setNotice("Live data refreshed from the database");
    }catch(e){setConnected(false);setNotice("Backend connection failed. Start FastAPI and refresh.");}
    finally{setBusy(false);}
  };
  useEffect(()=>{refresh();loadDemoScenarios().then(setScenarios).catch(()=>{});},[]);

  const chooseScenario=async()=>{
    if(!scenarioId)return;
    setBusy(true);
    try{
      const result=await applyDemoScenario(scenarioId);
      setAnalysis(null);
      await refresh();
      setNotice(`${result.scenario.name} loaded: ${result.batches_loaded} batches across ${result.stores_loaded} stores. Run analysis to generate fresh results.`);
      setActive("Dashboard");
    }catch(e){setNotice(e?.response?.data?.detail||"Could not load sample dataset.");}
    finally{setBusy(false);}
  };
  const doAnalysis=async()=>{
    setBusy(true);
    try{const a=await loadAnalysis(selectedStore==="all"?undefined:Number(selectedStore));setAnalysis(a);const r=await loadRecommendations();setRecommendations(r);await refresh();setNotice(`Analysis complete: ${a.total_batches} batches evaluated.`);}
    catch(e){setNotice(e?.response?.data?.detail||"Analysis failed. Check backend logs.");}
    finally{setBusy(false);}
  };
  const act=async(rec,action)=>{
    try{
      if(action==="approve")await approveRecommendation(rec.id);
      if(action==="reject")await rejectRecommendation(rec.id);
      if(action==="complete")await completeRecommendation(rec.id);
      const r=await loadRecommendations();setRecommendations(r);await refresh();setNotice(`Recommendation #${rec.id}: ${action} successful.`);
    }catch(e){setNotice(e?.response?.data?.detail||"Action failed. Check recommendation status.");}
  };
  const upload=async file=>{
    try{const r=await uploadInventory(file);setNotice(`Imported ${r.imported_records} rows; ${r.rejected_records} rejected. Run analysis for updated results.`);setShowUpload(false);setAnalysis(null);await refresh();}
    catch(e){setNotice(e?.response?.data?.detail||"CSV upload failed.");}
  };

  const storeInventory=useMemo(()=>inventory.filter(x=>selectedStore==="all"||String(x.store_id)===selectedStore),[inventory,selectedStore]);
  const filteredInventory=useMemo(()=>storeInventory.filter(x=>{
    const q=`${x.product_name} ${x.batch_code} ${x.store_name}`.toLowerCase();
    return q.includes(search.toLowerCase())&&(riskFilter==="All risk"||String(x.risk_level).toUpperCase()===riskFilter.toUpperCase());
  }),[storeInventory,search,riskFilter]);
  const transferRecs=recommendations.filter(r=>r.action_type==="TRANSFER"&&(selectedStore==="all"||String(r.source_store_id)===selectedStore||String(r.destination_store_id)===selectedStore));
  const pending=recommendations.filter(r=>r.status==="PENDING");
  const nav=[
    {name:"Dashboard",icon:LayoutDashboard,group:"WORKSPACE"},{name:"Inventory",icon:Package,group:"WORKSPACE"},
    {name:"Risk analysis",icon:Activity,group:"WORKSPACE"},{name:"Store matching",icon:MapPin,group:"WORKSPACE"},
    {name:"Recommendations",icon:Lightbulb,group:"WORKSPACE"},{name:"Approvals",icon:CheckCircle2,group:"MANAGEMENT"},
    {name:"Impact report",icon:ArrowUpRight,group:"MANAGEMENT"}
  ];
  const stats=[
    {label:"Total inventory",value:(analytics?.total_units??inventory.reduce((a,x)=>a+Number(x.quantity||0),0)).toLocaleString(),sub:`Across ${analytics?.total_stores??stores.length} stores`,icon:Boxes,tone:"blue"},
    {label:"At-risk surplus",value:(analytics?.surplus_inventory??0).toLocaleString(),sub:"Projected unsold units",icon:AlertTriangle,tone:"orange"},
    {label:"Estimated value protected",value:money(analytics?.estimated_value_protected??0),sub:"Net value from completed actions",icon:ShieldCheck,tone:"purple"},
    {label:"Pending actions",value:pending.length.toLocaleString(),sub:"Awaiting manager review",icon:Clock3,tone:"cyan"}
  ];

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={21}/></div><div><strong>ExpiryShield</strong><span>INVENTORY INTELLIGENCE</span></div></div>
      <div className="workspace-switch"><div className="store-avatar"><Store size={16}/></div><div><b>Retail Network</b><small>{stores.length} locations</small></div><ChevronDown size={15}/></div>
      <div className="nav-label">WORKSPACE</div>
      {nav.filter(n=>n.group==="WORKSPACE").map(n=><NavItem key={n.name} item={n} active={active===n.name} onClick={()=>setActive(n.name)}/>)}
      <div className="nav-label management-label">MANAGEMENT</div>
      {nav.filter(n=>n.group==="MANAGEMENT").map(n=><NavItem key={n.name} item={n} active={active===n.name} onClick={()=>setActive(n.name)}/>)}
      <div className="sidebar-bottom"><div className="help-card"><div className="help-icon"><CircleHelp size={17}/></div><b>Demo workspace</b><p>Choose one of five datasets to see different inventory outcomes.</p><button onClick={()=>setActive("Dashboard")}>Back to dashboard <ArrowRight size={13}/></button></div><NavItem item={{name:"Settings",icon:Settings}} active={active==="Settings"} onClick={()=>setActive("Settings")}/><div className="profile"><div className="profile-avatar">AA</div><div><b>Store administrator</b><small>ExpiryShield demo</small></div><MoreHorizontal size={18}/></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumb"><span>Workspace</span><span className="crumb-sep">/</span><b>{active}</b></div><div className="top-actions"><label className="search-box"><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search products, batches..."/></label><button className="icon-button notification"><Bell size={17}/></button><div className="user-chip"><div className="profile-avatar small">AA</div><span>Administrator</span></div></div></header>
      <div className="page-content">
        <div className="page-heading"><div><div className="eyebrow">INVENTORY INTELLIGENCE <span className={`connection ${connected?"online":""}`}><i/>{connected?"Live database":"Backend disconnected"}</span></div><h1>{active==="Dashboard"?"Inventory overview":active}</h1><p>{pageDescription(active)}</p></div><div className="heading-actions"><select className="scenario-select" value={scenarioId} onChange={e=>setScenarioId(e.target.value)} title="Choose sample dataset">{scenarios.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><button className="button secondary" onClick={chooseScenario} disabled={busy}><Play size={14}/> Load sample</button><button className="button secondary" onClick={refresh} disabled={busy}><RefreshCw size={14} className={busy?"spin":""}/> Refresh</button><button className="button primary" onClick={()=>setShowUpload(true)}><CloudUpload size={15}/> Import CSV</button></div></div>
        <div className="store-filter-row"><label>View data for <select value={selectedStore} onChange={e=>setSelectedStore(e.target.value)}><option value="all">All stores</option>{stores.map(s=><option key={s.id} value={s.id}>{s.store_name}</option>)}</select></label><span>Load a sample scenario or upload your own CSV. Each analysis is calculated from the selected database data.</span></div>
        {active==="Dashboard"&&<Dashboard stats={stats} analytics={analytics} inventory={filteredInventory} recommendations={recommendations} stores={stores} setActive={setActive} money={money}/>}
        {active==="Inventory"&&<InventoryPage inventory={filteredInventory} riskFilter={riskFilter} setRiskFilter={setRiskFilter} money={money}/>}
        {active==="Risk analysis"&&<RiskPage analysis={analysis} inventory={filteredInventory} onAnalyze={doAnalysis} busy={busy} money={money}/>}
        {active==="Store matching"&&<MatchingPage recommendations={transferRecs} stores={stores} money={money}/>}
        {active==="Recommendations"&&<RecommendationsPage recommendations={recommendations} money={money}/>}
        {active==="Approvals"&&<ApprovalsPage recommendations={recommendations} onAction={act} money={money}/>}
        {active==="Impact report"&&<ImpactPage analytics={analytics} money={money}/>}
        {active==="Settings"&&<SettingsPage scenarios={scenarios} scenarioId={scenarioId} setScenarioId={setScenarioId} onLoad={chooseScenario}/>}
      </div>
    </main>
    {showUpload&&<div className="modal-backdrop" onClick={()=>setShowUpload(false)}><div className="upload-modal" onClick={e=>e.stopPropagation()}><div className="modal-head"><div><h2>Import inventory dataset</h2><p>CSV import replaces the current demo dataset. Include daily_sales_per_day to power demand analysis.</p></div><button className="icon-button" onClick={()=>setShowUpload(false)}><X size={18}/></button></div><label className="drop-zone"><FileSpreadsheet size={30}/><b>Choose inventory CSV</b><span>Required: product_name, category, selling_price, cost_price, store_name, batch_code, quantity, expiry_date. Optional: daily_sales_per_day.</span><input type="file" accept=".csv" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0])}/></label><div className="sample-downloads"><b>Download one of the five sample datasets</b>{["01-transfer-opportunity.csv","02-urgent-discount.csv","03-fefo-rotation.csv","04-bundle-opportunity.csv","05-remote-store.csv"].map(f=><a className="sample-link" href={`/samples/${f}`} download key={f}>{f.replace(/^\d+-/,"").replaceAll("-"," ")} <Download size={13}/></a>)}</div></div></div>}
    {notice&&<div className="toast"><CheckCircle2 size={17}/>{notice}<button onClick={()=>setNotice("")}><X size={15}/></button></div>}
  </div>;
}

function pageDescription(page){return ({Dashboard:"Monitor expiry exposure and recommended actions across your retail network.",Inventory:"Inspect every product batch, quantity, expiry date and risk status.","Risk analysis":"Run demand-versus-stock calculations and inspect why each batch is at risk.","Store matching":"Find surplus stock at one location and demand gaps at another.",Recommendations:"Compare transfer, discount, bundle and FEFO actions using estimated net value.",Approvals:"Review recommendations and execute approved inventory actions.","Impact report":"Track inventory value, risk exposure and completed action outcomes.",Settings:"Select a scenario dataset and reset the demo workspace."})[page]||"ExpiryShield inventory intelligence."}
function NavItem({item,active,onClick}){const Icon=item.icon;return <button className={`nav-item ${active?"active":""}`} onClick={onClick}><Icon size={17}/><span>{item.name}</span></button>}
function RiskBadge({level}){const v=String(level||"LOW").toUpperCase();return <span className={`risk-badge ${v.toLowerCase()}`}>{v}</span>}
function StatCards({stats}){return <section className="stats-grid">{stats.map(s=><div className="stat-card" key={s.label}><div className="stat-top"><span>{s.label}</span><div className={`stat-icon ${s.tone}`}><s.icon size={18}/></div></div><div className="stat-value">{s.value}</div><div className="stat-foot"><span>{s.sub}</span></div></div>)}</section>}
function InventoryTable({inventory,money}){return <div className="panel inventory-panel"><div className="table-scroll"><table><thead><tr><th>PRODUCT / BATCH</th><th>STORE</th><th>STOCK</th><th>SELL PRICE</th><th>EXPIRES IN</th><th>RISK</th><th>SCORE</th></tr></thead><tbody>{inventory.map(x=><tr key={x.batch_id}><td><div className="product-cell"><div className="product-icon"><ShoppingBasket size={16}/></div><div><b>{x.product_name}</b><small>{x.batch_code}</small></div></div></td><td>{x.store_name}</td><td><b>{x.quantity}</b> units</td><td>{money(x.selling_price)}</td><td className={x.days_to_expiry<=7?"expiry-soon":""}>{x.days_to_expiry} days</td><td><RiskBadge level={x.risk_level}/></td><td>{Number(x.risk_score||0).toFixed(0)}/100</td></tr>)}</tbody></table>{!inventory.length&&<div className="empty-state">No inventory records. Load a sample dataset or import a CSV.</div>}</div></div>}
function Dashboard({stats,analytics,inventory,recommendations,stores,setActive,money}){const chart=(analytics?.expiry_distribution||[]).map(x=>({name:x.bracket,units:x.units}));return <><StatCards stats={stats}/><section className="dashboard-grid"><div className="panel trend-panel"><div className="panel-heading"><div><h2>Inventory by expiry window</h2><p>Units grouped by remaining shelf life</p></div></div><div className="chart-wrap">{chart.length?<ResponsiveContainer width="100%" height="100%"><BarChart data={chart}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef0f5"/><XAxis dataKey="name" tick={{fontSize:10}}/><YAxis tick={{fontSize:10}}/><Tooltip/><Bar dataKey="units" fill="#7869ef" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer>:<div className="empty-state">Load a dataset to populate expiry analytics.</div>}</div></div><div className="panel distribution-panel"><div className="panel-heading"><div><h2>Risk breakdown</h2><p>Current batch classification</p></div></div><div className="distribution-list">{[{name:"High / expired",value:analytics?.high_risk_batches??0},{name:"Medium",value:analytics?.medium_risk_batches??0},{name:"Low",value:analytics?.low_risk_batches??0}].map((x,i)=><div className="distribution-row" key={x.name}><div className="distribution-meta"><span>{x.name}</span><b>{x.value} batches</b></div><div className="progress-track"><div className={`progress-fill p${i}`} style={{width:`${Math.min(100,x.value/Math.max(1,analytics?.total_products||1)*100)}%`}}/></div></div>)}</div><div className="distribution-note"><span className="note-dot"/>Risk is calculated from shelf life and historical daily demand.</div></div></section><section className="lower-grid"><div className="panel inventory-panel"><div className="panel-heading"><div><h2>Priority inventory</h2><p>Highest urgency batches in the selected view</p></div><button className="text-button" onClick={()=>setActive("Inventory")}>View inventory <ArrowRight size={14}/></button></div><InventoryTable inventory={inventory.slice(0,6)} money={money}/></div><div className="right-stack"><div className="panel recommendations-panel"><div className="panel-heading"><div><h2>Recommended actions</h2><p>Freshly calculated opportunities</p></div><span className="count-badge">{recommendations.length} found</span></div>{recommendations.slice(0,3).map(r=><RecommendationCard key={r.id||r.batch_id} rec={r} money={money}/>) }{!recommendations.length&&<div className="empty-state">Run analysis to generate recommendations.</div>}<button className="panel-link" onClick={()=>setActive("Recommendations")}>View recommendations <ArrowRight size={14}/></button></div><div className="ai-card"><div className="ai-title"><div className="ai-orb"><Sparkles size={16}/></div><div><b>ExpiryShield insight</b><small>DATA-DRIVEN SUMMARY</small></div></div><p>{recommendations[0]?<><b>{recommendations[0].action_type} opportunity.</b> {recommendations[0].reason}</>:"Load a scenario and run analysis to generate an evidence-based inventory insight."}</p></div></div></section><div className="bottom-strip"><div><div className="bottom-icon"><Truck size={17}/></div><div><b>Cross-store network</b><span>{stores.length} stores connected · Matching uses demand gaps and distance</span></div></div><button onClick={()=>setActive("Store matching")}>Explore network <ArrowRight size={14}/></button></div></>}
function InventoryPage({inventory,riskFilter,setRiskFilter,money}){return <><div className="page-toolbar"><div><b>{inventory.length} batch records</b><span>Use the global search and store selector to narrow this list.</span></div><select value={riskFilter} onChange={e=>setRiskFilter(e.target.value)}><option>All risk</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option><option>EXPIRED</option></select></div><InventoryTable inventory={inventory} money={money}/></>}
function RiskPage({analysis,inventory,onAnalyze,busy,money}){const rows=analysis?.items||[];return <><div className="page-toolbar"><div><b>Demand and expiry assessment</b><span>Expected consumption = average daily demand × days remaining.</span></div><button className="button primary" onClick={onAnalyze} disabled={busy}><Activity size={15}/>{busy?"Analysing...":"Run risk analysis"}</button></div>{analysis&&<div className="stats-grid compact-stats">{[{label:"Batches analysed",value:analysis.total_batches},{label:"High risk",value:analysis.high_risk_count},{label:"Medium risk",value:analysis.medium_risk_count},{label:"Surplus value",value:money(analysis.total_surplus_value)}].map(x=><div className="stat-card" key={x.label}><div className="stat-top">{x.label}</div><div className="stat-value">{x.value}</div></div>)}</div>}<div className="panel inventory-panel"><div className="panel-heading"><div><h2>Batch-level risk explanation</h2><p>Risk score is calculated from urgency and projected unsold proportion.</p></div></div><div className="table-scroll"><table><thead><tr><th>PRODUCT</th><th>STORE</th><th>STOCK</th><th>DAILY DEMAND</th><th>EXPECTED TO SELL</th><th>SURPLUS</th><th>EXPIRES</th><th>RISK</th><th>WHY</th></tr></thead><tbody>{rows.map(x=><tr key={x.batch_id}><td><b>{x.product_name}</b><small className="table-sub">{x.batch_code}</small></td><td>{x.store_name}</td><td>{x.quantity}</td><td>{x.average_daily_demand}</td><td>{x.expected_consumption}</td><td>{x.surplus_quantity}</td><td>{x.days_to_expiry} days</td><td><RiskBadge level={x.risk_level}/></td><td className="reason-cell">{x.explanation}</td></tr>)}</tbody></table>{!rows.length&&<div className="empty-state">Click “Run risk analysis” to calculate results from the currently loaded dataset. {inventory.length} inventory batches are available.</div>}</div></div></>}
function MatchingPage({recommendations,stores,money}){return <><div className="stats-grid compact-stats">{[{label:"Stores in network",value:stores.length},{label:"Transfer matches",value:recommendations.length},{label:"Units proposed",value:recommendations.reduce((a,r)=>a+r.recommended_quantity,0)},{label:"Potential net benefit",value:money(recommendations.reduce((a,r)=>a+r.net_benefit,0))}].map(x=><div className="stat-card" key={x.label}><div className="stat-top">{x.label}</div><div className="stat-value">{x.value}</div></div>)}</div><div className="panel inventory-panel"><div className="panel-heading"><div><h2>Cross-store transfer opportunities</h2><p>Only matching products with source surplus, destination demand gap and feasible distance appear here.</p></div></div><div className="table-scroll"><table><thead><tr><th>PRODUCT</th><th>SOURCE STORE</th><th>DESTINATION</th><th>QUANTITY</th><th>DISTANCE</th><th>NET BENEFIT</th><th>STATUS</th></tr></thead><tbody>{recommendations.map(r=><tr key={r.id}><td><b>{r.product_name}</b><small className="table-sub">{r.batch_code}</small></td><td>{r.source_store_name}</td><td>{r.destination_store_name||"—"}</td><td>{r.recommended_quantity}</td><td>{Number(r.distance_km||0).toFixed(1)} km</td><td><b>{money(r.net_benefit)}</b></td><td><RiskBadge level={r.status==="COMPLETED"?"LOW":"MEDIUM"}/></td></tr>)}</tbody></table>{!recommendations.length&&<div className="empty-state">No economical transfer match in this dataset. This is an intentional outcome for scenarios where discount, bundle or FEFO is more suitable.</div>}</div></div></>}
function RecommendationCard({rec,money}){return <div className="recommendation"><div className="rec-top"><span className={`action-icon ${String(rec.action_type).toLowerCase()}`}>{rec.action_type==="TRANSFER"?<Truck size={16}/>:<Lightbulb size={16}/>}</span><span className="rec-type">{rec.action_type}</span><RiskBadge level={rec.risk_score>=70?"HIGH":rec.risk_score>=40?"MEDIUM":"LOW"}/></div><b>{rec.product_name}</b><p>{rec.reason}</p><div className="rec-bottom"><div><small>NET BENEFIT</small><strong>{money(rec.net_benefit)}</strong></div></div></div>}
function RecommendationsPage({recommendations,money}){return <div className="recommendation-grid">{recommendations.map(r=><div className="panel recommendation-detail" key={r.id}><RecommendationCard rec={r} money={money}/><div className="detail-meta"><span>Source: <b>{r.source_store_name}</b></span><span>Destination: <b>{r.destination_store_name||"In-store action"}</b></span><span>Quantity: <b>{r.recommended_quantity} units</b></span><span>Estimated cost: <b>{money(r.estimated_cost)}</b></span><span>Status: <b>{r.status}</b></span></div>{r.alternatives?.length>0&&<div className="alternatives"><b>Alternative actions</b>{r.alternatives.map((a,i)=><div key={i}><span>{a.action_type}</span><span>{a.feasibility}</span><b>{money(a.net_benefit)}</b></div>)}</div>}</div>)}{!recommendations.length&&<div className="empty-state">No recommendations yet. Load a sample and run risk analysis.</div>}</div>}
function ApprovalsPage({recommendations,onAction,money}){return <div className="panel inventory-panel"><div className="panel-heading"><div><h2>Recommendation review queue</h2><p>Approve, reject or execute generated actions.</p></div></div><div className="approval-list">{recommendations.map(r=><div className="approval-row" key={r.id}><div className="approval-main"><b>{r.product_name} · {r.action_type}</b><span>{r.source_store_name} {r.destination_store_name?`→ ${r.destination_store_name}`:"· in-store action"} · {r.recommended_quantity} units · {money(r.net_benefit)} net</span><small>{r.reason}</small></div><RiskBadge level={r.status==="COMPLETED"?"LOW":r.status==="REJECTED"?"EXPIRED":"MEDIUM"}/><div className="approval-buttons">{r.status==="PENDING"&&<><button className="button primary" onClick={()=>onAction(r,"approve")}>Approve</button><button className="button secondary" onClick={()=>onAction(r,"reject")}>Reject</button></>}{r.status==="APPROVED"&&<button className="button primary" onClick={()=>onAction(r,"complete")}>Execute</button>}{r.status!=="PENDING"&&r.status!=="APPROVED"&&<span className="status-text">{r.status}</span>}</div></div>)}{!recommendations.length&&<div className="empty-state">No actions to review. Run analysis first.</div>}</div></div>}
function ImpactPage({analytics,money}){const i=analytics?.impact_summary||{};return <><div className="stats-grid compact-stats">{[{label:"Total inventory units",value:analytics?.total_units??0},{label:"Potential surplus",value:analytics?.surplus_inventory??0},{label:"Estimated net value protected",value:money(analytics?.estimated_value_protected??0)},{label:"Completed transfers",value:analytics?.completed_transfers??0}].map(x=><div className="stat-card" key={x.label}><div className="stat-top">{x.label}</div><div className="stat-value">{x.value}</div></div>)}</div><div className="panel impact-panel"><div className="panel-heading"><div><h2>Impact accounting</h2><p>Separate completed outcomes from forecast opportunities.</p></div></div><div className="impact-grid">{Object.entries(i).map(([k,v])=><div><span>{titleCase(k.replaceAll("_"," "))}</span><b>{typeof v==="number"?money(v):String(v)}</b></div>)}</div><p className="muted-note">Potential value is an estimate generated from the selected demo dataset. Only completed actions should be described as realized impact.</p></div></>}
function SettingsPage({scenarios,scenarioId,setScenarioId,onLoad}){return <div className="panel settings-panel"><h2>Demo data management</h2><p>Each sample replaces the current demo inventory, stores, sales history and pending recommendations. Choose a scenario, load it, then run risk analysis.</p><select value={scenarioId} onChange={e=>setScenarioId(e.target.value)}>{scenarios.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><button className="button primary" onClick={onLoad}><RotateCcw size={14}/> Load selected scenario</button><div className="scenario-catalog">{scenarios.map(s=><div key={s.id}><b>{s.name}</b><span>{s.description}</span></div>)}</div></div>}
export default App;
