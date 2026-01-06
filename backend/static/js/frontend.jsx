const { useState, useEffect, useRef } = React;

function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}

function MonthPicker({year, month, onChange}){
  const years = [];
  const now = new Date();
  for(let y = now.getFullYear()-2; y <= now.getFullYear(); y++) years.push(y);
  return (
    <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:12}}>
      <label style={{fontSize:14}}>Month</label>
      <select value={month} onChange={e=>onChange(year, parseInt(e.target.value))}>
        {Array.from({length:12}, (_,i)=>i+1).map(m=> (
          <option value={m} key={m}>{m}</option>
        ))}
      </select>
      <label style={{fontSize:14}}>Year</label>
      <select value={year} onChange={e=>onChange(parseInt(e.target.value), month)}>
        {years.map(y=> <option value={y} key={y}>{y}</option>)}
      </select>
    </div>
  );
}

function HabitRow({h, allowToggle, onToggleToday, pending}){
  const today = new Date().getDate();
  const isCompletedToday = h.days && h.days.some(d=>d.day === today && d.completed);
  const label = isCompletedToday ? 'Completed' : 'To Do';
  const btnStyle = isCompletedToday ? {background:'#10b981'} : {};
  return (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 12px',background:'#fff',borderRadius:8,marginBottom:8,boxShadow:'0 4px 10px rgba(15,23,42,0.04)'}}>
      <div>
        <div style={{fontWeight:600}}>{h.title}</div>
        <div style={{color:'#6b7280',fontSize:13}}>{h.percentage}% ({h.completed_count}/{h.days.length})</div>
      </div>
      <div>
        {allowToggle ? (
          <button className="btn" style={btnStyle} onClick={()=>onToggleToday(h.id)} disabled={pending}>
            {pending ? 'Updating...' : label}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function App({mode='dashboard'}){
  // map friendly page modes to internal modes
  if(mode === 'monthly_insights') mode = 'monthly';
  if(mode === 'yearly_summary') mode = 'yearly';
  if(mode === 'manage_habits') mode = 'habits';
  const now = new Date();
  const [year,setYear] = useState(now.getFullYear());
  const [month,setMonth] = useState(now.getMonth()+1);
  const [habits,setHabits] = useState([]);
  const [selectedHabits, setSelectedHabits] = useState([]);
  const pendingRef = useRef(new Set());
  const [monthlyData,setMonthlyData] = useState(null);
  const [yearlyData,setYearlyData] = useState(null);
  const monthlyRef = useRef(null);
  const yearlyRef = useRef(null);
  const monthlyChartRef = useRef(null);
  const yearlyChartRef = useRef(null);

  useEffect(()=>{ fetchAll(); }, [year, month]);

  // Refresh data when user returns to the tab (ensure UI matches server)
  // useEffect(()=>{
  //   function handleVisibility(){
  //     if(document.visibilityState === 'visible'){
  //       console.log('Tab visible — refreshing habits');
  //       fetchAll();
  //     }
  //   }
  //   window.addEventListener('focus', handleVisibility);
  //   document.addEventListener('visibilitychange', handleVisibility);
  //   return ()=>{
  //     window.removeEventListener('focus', handleVisibility);
  //     document.removeEventListener('visibilitychange', handleVisibility);
  //   }
  // }, [year, month]);

  // helper to format today's full date
  function todayFullDate(){
    const d = new Date();
    return d.toLocaleDateString(undefined, {weekday:'short', year:'numeric', month:'short', day:'numeric'});
  }

  // NOTE: No local persistence — backend is single source of truth.

  function fetchAll(){
    console.log('fetchAll start', year, month);
    // Replace local state with authoritative server response for selected month
    fetch(`/api/habits-for-month/?year=${year}&month=${month}`).then(r=>r.json()).then(d=>{
      const serverHabits = d.habits || [];
      setHabits(serverHabits.map(s => {
        const today = new Date();
        const todayDay = today.getDate();

        let days = (s.days || []).map(sd => ({...sd}));

        // 🔥 FIX: ensure today's entry exists
        if (!days.some(d => d.day === todayDay)) {
          days.push({
            day: todayDay,
            completed: false
          });
        }

        const completed_count = days.filter(dy=>dy.completed).length;
        const percentage = days.length ? Math.round((completed_count / days.length) * 1000)/10 : 0;
        return {...s, days, completed_count, percentage};
      }));
      console.log('fetchAll setHabits', serverHabits.length);
    });
    fetch(`/api/monthly-progress/?year=${year}&month=${month}`).then(r=>r.json()).then(d=> setMonthlyData(d));
    fetch(`/api/yearly-progress/?year=${year}`).then(r=>r.json()).then(d=> setYearlyData(d));
  }

  useEffect(()=>{
    if(!monthlyData) return;
    if(!monthlyRef.current) return;
    const ctx = monthlyRef.current.getContext('2d');
    if(monthlyChartRef.current) monthlyChartRef.current.destroy();

    // If user selected specific habits, render per-habit binary lines
    if(selectedHabits && selectedHabits.length > 0){
      const datasets = selectedHabits.map((h, idx)=>{
        const hue = (idx*60) % 360;
        const color = `hsl(${hue} 70% 45%)`;
        const data = h.days.map(d=> d.completed ? 1 : 0);
        return {label: h.title, data, borderColor: color, backgroundColor: 'transparent', fill:false, tension:0.2}
      });
      monthlyChartRef.current = new Chart(ctx, {type:'line', data:{labels: monthlyData.labels, datasets}, options:{responsive:true, maintainAspectRatio:false, scales:{y:{beginAtZero:true, max:1, ticks:{stepSize:1}}}}});
      return;
    }

    // default: overall daily percentage
    monthlyChartRef.current = new Chart(ctx, {
      type:'line',
      data:{labels: monthlyData.labels, datasets:[{label:'Daily %', data: monthlyData.percentages, borderColor:'rgba(37,99,235,0.9)', backgroundColor:'rgba(37,99,235,0.2)', fill:true, tension:0.2}]},
      options:{responsive:true, maintainAspectRatio:false, scales:{y:{beginAtZero:true, max:100, ticks:{stepSize:10}}}}
    });
  }, [monthlyData, selectedHabits]);

  useEffect(()=>{
    if(!yearlyData) return;
    if(!yearlyRef.current) return;
    const ctx = yearlyRef.current.getContext('2d');
    if(yearlyChartRef.current) yearlyChartRef.current.destroy();
    yearlyChartRef.current = new Chart(ctx, {
      type:'line',
      data:{labels: yearlyData.months, datasets:[{label:'Monthly %', data: yearlyData.percentages, borderColor:'rgba(16,185,129,0.9)', backgroundColor:'rgba(16,185,129,0.2)', fill:true, tension:0.2}]},
      options:{responsive:true, maintainAspectRatio:false, scales:{y:{beginAtZero:true, max:100, ticks:{stepSize:10}}}}
    });
  }, [yearlyData]);

  function onChange(y,m){ setYear(y); setMonth(m); }

  async function onToggleToday(habitId) {
    if (pendingRef.current.has(habitId)) return;
    pendingRef.current.add(habitId);

    const today = new Date().getDate();
    const habit = habits.find(h => h.id === habitId);
    const completedToday = habit?.days?.some(d => d.day === today && d.completed);
    const desiredCompleted = !completedToday;

    const csrftoken = getCookie('csrftoken');
    function getLocalISODate() {
      const d = new Date();
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }

    const todayISO = getLocalISODate();
    try {
      const res = await fetch('/api/toggle-entry/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          habit_id: habitId,
          completed: desiredCompleted,
          date: todayISO
        })
      });

      if (res.ok) {
        fetchAll();
      } else {
        alert(await res.text());
      }
    } finally {
      pendingRef.current.delete(habitId);
    }
  }


  async function addHabit(title){
    if(!title || !title.trim()) return;
    const csrftoken = getCookie('csrftoken');
    const res = await fetch('/add/', {
      method:'POST',
      headers: {'X-CSRFToken': csrftoken, 'Content-Type':'application/x-www-form-urlencoded'},
      body: new URLSearchParams({title: title.trim()})
    });
    if(res.ok){ setNewTitle(''); fetchAll(); }
    else{ alert('Failed to add'); }
  }

  // Daily journal handlers
  const [journalDate, setJournalDate] = useState(new Date().toISOString().slice(0,10));
  const [journalText, setJournalText] = useState('');
  const [journalSaved, setJournalSaved] = useState(false);
  const [journalEditing, setJournalEditing] = useState(true);

  useEffect(()=>{
    if(mode !== 'daily_journal') return;
    fetch(`/api/journal/?date=${journalDate}`).then(r=>r.json()).then(d=>{
      setJournalText(d.text || '');
      const has = (d.text && d.text.length>0);
      setJournalSaved(has);
      setJournalEditing(!has);
    });
  }, [mode, journalDate]);

  async function saveJournal(){
    const csrftoken = getCookie('csrftoken');
    const res = await fetch('/api/journal/', {
      method:'POST',
      headers: {'X-CSRFToken': csrftoken, 'Content-Type':'application/json'},
      body: JSON.stringify({date: journalDate, text: journalText})
    });
    if(res.ok){
      setJournalSaved(true);
      setJournalEditing(false);
    } else alert('Save failed');
  }

  const allowToggle = (year === now.getFullYear() && month === (now.getMonth()+1));
  const [newTitle, setNewTitle] = useState('');

  return (
    <div>
      {/* Top controls */}
      <div style={{marginBottom:12}}>
        {mode !== 'dashboard' && mode !== 'habits' && <MonthPicker year={year} month={month} onChange={onChange} />}
      </div>

      {/* Dashboard: only habit list and today's date */}
      {mode === 'dashboard' && (
        <div>
          <h2 style={{marginTop:0}}>Today — {todayFullDate()}</h2>
          {habits.map(h=> (
            <div key={h.id} style={{marginBottom:8}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',background:'#fff',padding:12,borderRadius:8}}>
                <div>
                  <div style={{fontWeight:700}}>{h.title}</div>
                  <div style={{color:'#6b7280',fontSize:13}}>{h.percentage}% this month</div>
                </div>
                <div>
                  {allowToggle ? (
                    (()=>{
                      const today = (new Date()).getDate();
                      const completedToday = h.days && h.days.some(d=>d.day === today && d.completed);
                      const label = completedToday ? 'Completed' : 'To Do';
                      const style = completedToday ? {background:'#10b981'} : {};
                      const isPending = pendingRef.current.has(h.id);
                      return <button className="btn" style={style} onClick={()=>onToggleToday(h.id)} disabled={isPending}>{isPending ? 'Updating...' : label}</button>;
                    })()
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Habits management: add + full list */}
      {mode === 'habits' && (
        <div style={{display:'grid',gridTemplateColumns:'1fr',gap:12}}>
          <div style={{background:'#fff',padding:12,borderRadius:10}}>
            <h3 style={{marginTop:0}}>Add habit</h3>
            <div style={{display:'flex',gap:8}}>
              <input value={newTitle} onChange={e=>setNewTitle(e.target.value)} placeholder="New habit" style={{flex:1,padding:8,borderRadius:8,border:'1px solid #e6eef7'}} />
              <button className="btn" onClick={()=>addHabit(newTitle)}>Add</button>
            </div>
          </div>
          <div>
            <h3 style={{marginTop:0}}>All habits</h3>
            {habits.map(h=> <HabitRow key={h.id} h={h} allowToggle={allowToggle} onToggleToday={onToggleToday} pending={pendingRef.current.has(h.id)} />)}
          </div>
        </div>
      )}

      {/* Monthly insights: only monthly chart and small summary */}
      {mode === 'monthly' && (
        <div style={{background:'#fff',padding:12,borderRadius:10}}>
          <h3 style={{marginTop:0}}>Monthly Insights — {month}/{year}</h3>
          <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:12}}>
            {habits.map(h=>{
              const selected = selectedHabits.find(s=>s.id===h.id);
              return (
                <button key={h.id} onClick={()=>{
                  if(selected){ setSelectedHabits(selectedHabits.filter(s=>s.id!==h.id)); }
                  else{ setSelectedHabits([...selectedHabits, h]); }
                }} className="btn" style={{background: selected ? '#2563eb' : '#eef2ff', color: selected ? '#fff' : '#0f172a'}}>
                  {h.title}
                </button>
              )
            })}
          </div>
          <div style={{height:360}}><canvas ref={monthlyRef}></canvas></div>
        </div>
      )}

      {/* Yearly summary: only yearly chart */}
      {mode === 'yearly' && (
        <div style={{background:'#fff',padding:12,borderRadius:10}}>
          <h3 style={{marginTop:0}}>Yearly Summary — {year}</h3>
          <div style={{height:360}}><canvas ref={yearlyRef}></canvas></div>
        </div>
      )}

      {mode === 'daily_journal' && (
        <div style={{background:'#fff',padding:12,borderRadius:10}}>
          <h3 style={{marginTop:0}}>Daily Journal</h3>
          <div style={{display:'flex',gap:8,marginBottom:8,alignItems:'center'}}>
            <label>Date:</label>
            <input type="date" value={journalDate} onChange={e=>{setJournalDate(e.target.value); setJournalEditing(true);}} />
            {!journalSaved || journalEditing ? (
              <button className="btn" onClick={saveJournal}>Save</button>
            ) : (
              <button className="btn" onClick={()=>setJournalEditing(true)}>Edit</button>
            )}
          </div>
          {journalSaved && !journalEditing ? (
            <div style={{whiteSpace:'pre-wrap',padding:12,borderRadius:8,background:'#f8fafc'}}>{journalText}</div>
          ) : (
            <textarea value={journalText} onChange={e=>setJournalText(e.target.value)} style={{width:'100%',height:300,padding:12,borderRadius:8,border:'1px solid #e6eef7'}} />
          )}
        </div>
      )}
    </div>
  );
}

const mount = document.getElementById('habit-app');
if(mount){
  const mode = mount.dataset.mode || 'dashboard';
  ReactDOM.createRoot(mount).render(React.createElement(App, {mode}));
}


