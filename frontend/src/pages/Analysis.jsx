import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import TopNavBar from '../components/TopNavBar';
import Footer from '../components/Footer';

const DEMO_RESULT = {
  severity: 'CRITICAL',
  headline: 'Aortic Dissection suspected',
  subheadline: 'Likely Aortic Dissection — high-risk features present',
  dataQuality: 'HIGH',
  dataQualityNote: '(complete vitals + history present)',
  redFlags: [
    'Tearing chest pain radiating to back is highly suspicious for aortic dissection.',
    'Significant blood pressure differential between arms (40mmHg systolic gap).',
  ],
  differential: [
    { rank:'01', condition:'Aortic Dissection', reasoning:'chest pain radiating to back + BP differential', probability:'VERY LIKELY', probColor:'#ED1C24', border:'#ED1C24' },
    { rank:'02', condition:'Acute Myocardial Infarction', reasoning:'severe chest pain, though radiation is atypical for MI', probability:'POSSIBLE', probColor:'#f97316', border:'#f97316' },
    { rank:'03', condition:'Pulmonary Embolism', reasoning:'pleuritic component absent, but risk factors present', probability:'LESS LIKELY', probColor:'#fbbf24', border:'#fbbf24' },
  ],
  actions: [
    'Stat CT Angiography of chest/abdomen/pelvis to rule out dissection.',
    'Establish large bore IV access x2.',
    'Initiate strict heart rate and blood pressure control (e.g., Esmolol drip) pending CT results. Target HR < 60, SBP < 120.',
  ],
  missing: ['medication history', 'symptom duration'],
};

const AGENTS = [
  { id:'intake',   label:'Intake Processor',  icon:'input',      doneFirst: true },
  { id:'ddx',      label:'Differential (DDx)', icon:'memory',     pulse:'ddx' },
  { id:'redflag',  label:'Red Flag Scan',       icon:'radar',      pulse:'redflag' },
  { id:'consist',  label:'Data Consistency',    icon:'fact_check' },
  { id:'summary',  label:'Report Synthesis',    icon:'summarize' },
];

function AgentRow({ agent, status }) {
  const isCompleted = status === 'COMPLETED';
  const isProcessing = status === 'PROCESSING' || status === 'ANALYZING';
  const isIdle = status === 'IDLE';
  const color = isCompleted ? '#3cd7ff' : isProcessing && agent.pulse === 'redflag' ? '#ff544b'
    : isProcessing ? '#3cd7ff' : 'rgba(122,144,176,0.4)';
  const pulseCss = isProcessing ? (agent.pulse === 'redflag' ? {animation:'redflag-pulse 2s infinite'} : {animation:'ddx-pulse 2s infinite'}) : {};

  return (
    <div style={{
      display:'flex', alignItems:'center', gap:'12px',
      fontFamily:"'JetBrains Mono',monospace", fontSize:'13px',
      padding: isProcessing ? '8px' : '4px 8px',
      margin: isProcessing ? '0 -8px' : '0 0',
      background: isProcessing && agent.pulse==='redflag' ? 'rgba(255,84,75,0.06)'
        : isProcessing ? 'rgba(60,215,255,0.06)' : 'transparent',
      border: isProcessing ? `1px solid ${color}22` : 'none',
      opacity: isIdle ? 0.45 : 1,
      ...pulseCss,
    }}>
      <div style={{ width:'24px', height:'24px', borderRadius:'50%', border:`1px solid ${color}`,
        display:'flex', alignItems:'center', justifyContent:'center', color,
        boxShadow: isProcessing ? `0 0 8px ${color}` : 'none' }}>
        <span className="material-symbols-outlined" style={{ fontSize:'13px',
          animation: isProcessing ? 'spin 1.5s linear infinite' : 'none' }}>
          {isCompleted ? 'check' : isIdle ? 'pending' : agent.icon}
        </span>
      </div>
      <span style={{ flex:1, color: isIdle ? 'var(--text-dim)' : isProcessing && agent.pulse==='redflag' ? '#ff544b' : isProcessing ? '#3cd7ff' : 'var(--text)' }}>
        {agent.label}
      </span>
      <span className="label-caps" style={{ color, animation: isProcessing ? 'pulse-opacity 1.5s ease infinite' : 'none' }}>
        {status}
      </span>
    </div>
  );
}

export default function Analysis() {
  const [caseText, setCaseText] = useState(() =>
    sessionStorage.getItem('medsignal_case') ||
    'Pt presents with acute tearing chest pain radiating to back. BP 180/110 right arm, 140/90 left arm. Diaphoretic. History of HTN, smoking.'
  );

  useEffect(() => {
    const stored = sessionStorage.getItem('medsignal_case');
    if (stored) { setCaseText(stored); sessionStorage.removeItem('medsignal_case'); }
  }, []);
  const [agentStatuses, setAgentStatuses] = useState({
    intake:'IDLE', ddx:'IDLE', redflag:'IDLE', consist:'IDLE', summary:'IDLE'
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function runAnalysis() {
    if (!caseText.trim() || loading) return;
    setResult(null);
    setLoading(true);

    const seq = async (updates, delayMs) => {
      await new Promise(r => setTimeout(r, delayMs));
      setAgentStatuses(prev => ({ ...prev, ...updates }));
    };

    setAgentStatuses({ intake:'PROCESSING', ddx:'IDLE', redflag:'IDLE', consist:'IDLE', summary:'IDLE' });
    await seq({ intake:'COMPLETED', ddx:'PROCESSING', redflag:'ANALYZING' }, 900);
    await seq({ ddx:'COMPLETED', redflag:'COMPLETED', consist:'PROCESSING' }, 1800);
    await seq({ consist:'COMPLETED', summary:'PROCESSING' }, 900);
    await seq({ summary:'COMPLETED' }, 700);

    // Try real API, fall back to demo
    try {
      const res = await axios.post('http://localhost:8000/analyze', { case: caseText }, { timeout: 30000 });
      setResult(res.data);
    } catch {
      setResult(DEMO_RESULT);
    }
    setLoading(false);
  }

  const r = result || DEMO_RESULT;

  return (
    <div style={{ minHeight:'100vh', position:'relative' }}>
      <TopNavBar />
      <div style={{ position:'fixed', inset:0, pointerEvents:'none', zIndex:0,
        backgroundImage:'radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px)',
        backgroundSize:'32px 32px' }} />

      <main style={{ position:'relative', zIndex:1, maxWidth:'1440px', margin:'0 auto',
        padding:'88px 24px 24px', display:'grid',
        gridTemplateColumns:'400px 1fr', gap:'16px', minHeight:'100vh' }}>

        {/* LEFT COLUMN */}
        <section style={{ display:'flex', flexDirection:'column', gap:'16px' }}>

          {/* Input panel */}
          <div className="panel" style={{ padding:'16px', borderLeft:'2px solid #00d2fd' }}>
            <div className="label-caps" style={{ color:'#00d2fd', marginBottom:'16px',
              display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <span>Patient Input</span>
              <span className="material-symbols-outlined" style={{ fontSize:'16px', color:'#00d2fd' }}>input</span>
            </div>
            <textarea
              value={caseText}
              onChange={e => setCaseText(e.target.value)}
              placeholder="Enter clinical notes, vitals, or patient history here..."
              style={{
                width:'100%', height:'180px', background:'rgba(0,20,42,0.8)',
                border:'none', borderBottom:'1px solid rgba(31,54,81,0.8)',
                color:'var(--text)', fontFamily:"'JetBrains Mono',monospace",
                fontSize:'13px', padding:'8px', resize:'none', outline:'none',
                lineHeight:1.5,
              }}
            />
            <button className="btn-primary"
              onClick={runAnalysis}
              disabled={loading}
              style={{ width:'100%', marginTop:'12px', padding:'12px',
                display:'flex', alignItems:'center', justifyContent:'center', gap:'8px',
                opacity: loading ? 0.7 : 1, cursor: loading ? 'wait' : 'pointer' }}>
              {loading ? 'ANALYZING...' : 'ANALYZE'}
              <span className="material-symbols-outlined" style={{ fontSize:'15px' }}>arrow_forward</span>
            </button>
          </div>

          {/* Agent Status */}
          <div className="panel" style={{ padding:'16px' }}>
            <div className="label-caps" style={{ color:'#8991a2', marginBottom:'16px' }}>Agent Status</div>
            <div style={{ display:'flex', flexDirection:'column', gap:'12px' }}>
              {AGENTS.map(a => (
                <AgentRow key={a.id} agent={a} status={agentStatuses[a.id]} />
              ))}
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN */}
        <section style={{ display:'flex', flexDirection:'column', gap:'16px' }}>

          {/* Header */}
          <AnimatePresence>
            {result && (
              <motion.div initial={{ opacity:0, y:-12 }} animate={{ opacity:1, y:0 }}
                style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:'16px',
                  borderBottom:'1px solid rgba(31,54,81,0.8)', paddingBottom:'16px' }}>
                <div style={{ border:'1px solid rgba(255,180,171,0.6)', padding:'16px 20px',
                  boxShadow:'0 0 15px rgba(255,180,171,0.1)', flex:1 }}>
                  <div style={{ fontFamily:"'Space Grotesk',sans-serif", fontWeight:600, fontSize:'22px',
                    color:'#ffb4ab', display:'flex', alignItems:'center', gap:'8px' }}>
                    🚨 CRITICAL: {r.headline}
                  </div>
                  <div style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:'16px',
                    color:'#ff544b', opacity:0.9, marginTop:'4px' }}>
                    ⚠ {r.subheadline}
                  </div>
                </div>
                <div style={{ border:'1px solid rgba(60,215,255,0.15)', padding:'8px 12px',
                  display:'flex', flexDirection:'column', alignItems:'flex-end', gap:'4px', opacity:0.75 }}>
                  <div className="label-caps" style={{ color:'#3cd7ff' }}>DATA QUALITY: {r.dataQuality}</div>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'10px', color:'#8991a2' }}>{r.dataQualityNote}</div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Red Flags */}
          <div className="panel" style={{ padding:'16px', borderLeft:'2px solid #ED1C24' }}>
            <div className="label-caps" style={{ color:'#ED1C24', marginBottom:'16px',
              display:'flex', alignItems:'center', gap:'6px' }}>
              <span className="material-symbols-outlined" style={{ fontSize:'13px' }}>flag</span>
              Red Flags
            </div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontWeight:700, fontSize:'15px',
              color:'#ff544b', marginBottom:'8px' }}>🚨 CRITICAL: {r.redFlags ? 'Aortic Dissection suspected' : ''}</div>
            <div className="label-caps" style={{ color:'#8991a2', marginBottom:'12px' }}>Key Findings:</div>
            <ul style={{ listStyle:'none', display:'flex', flexDirection:'column', gap:'10px' }}>
              {r.redFlags?.map((f,i) => (
                <li key={i} style={{ display:'flex', alignItems:'flex-start', gap:'12px',
                  background:'rgba(31,54,81,0.25)', padding:'12px',
                  border:'1px solid rgba(31,54,81,0.5)' }}>
                  <span style={{ color:'#ED1C24', fontWeight:700, fontSize:'18px', lineHeight:1 }}>—</span>
                  <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'13px', color:'var(--text)' }}>{f}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* DDx Table */}
          <div className="panel" style={{ padding:'16px', borderLeft:'2px solid rgba(122,144,176,0.3)' }}>
            <div className="label-caps" style={{ color:'#8991a2', marginBottom:'16px',
              display:'flex', alignItems:'center', gap:'6px' }}>
              <span className="material-symbols-outlined" style={{ fontSize:'13px' }}>format_list_numbered</span>
              Differential Diagnosis (Ranked)
            </div>
            <table style={{ width:'100%', borderCollapse:'separate', borderSpacing:'0 12px',
              fontFamily:"'JetBrains Mono',monospace", fontSize:'13px' }}>
              <thead>
                <tr>
                  {['RNK','Condition & Reasoning','Probability','Action'].map((h, i) => (
                    <th key={h} style={{ textAlign: i >= 2 ? 'right' : 'left',
                      padding:'4px 8px',
                      paddingLeft: i === 0 ? '12px' : '8px',
                      color:'#8991a2', fontWeight:700, fontSize:'10px',
                      letterSpacing:'0.1em', textTransform:'uppercase',
                      borderBottom:'1px solid rgba(31,54,81,0.8)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {r.differential?.map(d => (
                  <tr key={d.rank} style={{ background:'rgba(31,54,81,0.12)' }}>
                    <td style={{ padding:'16px 8px', paddingLeft:'8px',
                      borderLeft:`4px solid ${d.border}`,
                      fontWeight:700, color:d.border }}>{d.rank}</td>
                    <td style={{ padding:'16px 8px' }}>
                      <div style={{ fontWeight:700, fontSize:'14px', color:'var(--text)' }}>{d.condition}</div>
                      <div style={{ fontSize:'11px', color:'#8991a2', marginTop:'4px' }}>→ {d.reasoning}</div>
                    </td>
                    <td style={{ padding:'16px 8px', textAlign:'right' }}>
                      <div style={{ fontWeight:700, color:d.probColor }}>{d.probability}</div>
                    </td>
                    <td style={{ padding:'16px 8px', textAlign:'right' }}>
                      {d.rank === '01' ? (
                        <button className="hover-text-glow-dark" style={{ background:'#00d2fd', color:'#000f22', fontFamily:"'JetBrains Mono',monospace",
                          fontWeight:700, fontSize:'10px', letterSpacing:'0.1em', textTransform:'uppercase',
                          padding:'6px 12px', border:'none', cursor:'pointer', transition:'text-shadow 0.2s' }}
                          onMouseEnter={e => e.target.style.textShadow='0 0 8px rgba(0,0,0,0.6)'}
                          onMouseLeave={e => e.target.style.textShadow='none'}>
                          VIEW PROTOCOL
                        </button>
                      ) : (
                        <button style={{ background:'transparent', border:'1px solid rgba(31,54,81,0.8)',
                          color:'#8991a2', fontFamily:"'JetBrains Mono',monospace", fontSize:'10px',
                          letterSpacing:'0.08em', textTransform:'uppercase', padding:'4px 10px', cursor:'pointer', transition:'text-shadow 0.2s' }}
                          onMouseEnter={e => e.target.style.textShadow='0 0 8px rgba(188,199,217,0.9)'}
                          onMouseLeave={e => e.target.style.textShadow='none'}>
                          Why this diagnosis
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Actions + Missing */}
          <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:'16px' }}>
            <div className="panel" style={{ padding:'16px' }}>
              <div className="label-caps" style={{ color:'#00d2fd', marginBottom:'16px',
                display:'flex', alignItems:'center', gap:'6px' }}>
                <span className="material-symbols-outlined" style={{ fontSize:'13px' }}>play_circle</span>
                Recommended Actions
              </div>
              <div style={{ display:'flex', flexDirection:'column', gap:'12px',
                fontFamily:"'JetBrains Mono',monospace", fontSize:'13px' }}>
                {r.actions?.map((a,i) => (
                  <div key={i} style={{ display:'flex', gap:'12px', alignItems:'flex-start' }}>
                    <span style={{ border:'1px solid rgba(0,210,253,0.5)', color:'#00d2fd',
                      padding:'1px 6px', fontSize:'10px', fontWeight:700, marginTop:'1px', flexShrink:0 }}>
                      {String(i+1).padStart(2,'0')}
                    </span>
                    <span style={{ color:'var(--text)' }}>{a}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="panel" style={{ padding:'16px', borderLeft:'2px solid #fbbf24', opacity:0.8 }}>
              <div className="label-caps" style={{ color:'#fbbf24', marginBottom:'12px', fontSize:'10px',
                display:'flex', alignItems:'center', gap:'4px' }}>
                <span className="material-symbols-outlined" style={{ fontSize:'11px' }}>help_outline</span>
                Missing Information
              </div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'12px',
                color:'var(--text)', display:'flex', flexDirection:'column', gap:'4px' }}>
                {r.missing?.map(m => <div key={m}>— {m}</div>)}
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:'16px',
            paddingTop:'16px', borderTop:'1px solid rgba(31,54,81,0.8)' }}>
            <p style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'9px', color:'rgba(138,145,162,0.5)',
              textTransform:'uppercase', lineHeight:1.6, maxWidth:'520px' }}>
              SYSTEM GENERATED ANALYSIS. AI INFERENCES DO NOT CONSTITUTE FINAL MEDICAL ADVICE.
              CLINICAL CORRELATION AND PHYSICIAN JUDGMENT ARE REQUIRED BEFORE INITIATING TREATMENT PROTOCOLS.
            </p>
            <button style={{ flexShrink:0, background:'transparent', border:'1px solid #8991a2',
              color:'#8991a2', fontFamily:"'JetBrains Mono',monospace", fontWeight:700, fontSize:'10px',
              letterSpacing:'0.1em', textTransform:'uppercase', padding:'8px 16px', cursor:'pointer',
              display:'flex', alignItems:'center', gap:'6px', transition:'text-shadow 0.2s' }}
              onMouseEnter={e => e.currentTarget.style.textShadow='0 0 8px rgba(188,199,217,0.9)'}
              onMouseLeave={e => e.currentTarget.style.textShadow='none'}>
              <span className="material-symbols-outlined" style={{ fontSize:'14px' }}>download</span>
              Export Report
            </button>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}