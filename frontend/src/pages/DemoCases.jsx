import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import TopNavBar from '../components/TopNavBar';
import Footer from '../components/Footer';

const CASES = [
  {
    id: 1,
    title: '65M — Severe Chest Pain',
    badge: { text:'⚠ Dangerous Drug Combination', color:'#ED1C24', bg:'rgba(237,28,36,0.08)' },
    symptoms: [
      { text:'Smoker (risk factor)', dot:'#00d4ff' },
      { text:'Diabetic (chronic condition)', dot:'#00d4ff' },
      { text:'Warfarin + Clarithromycin', dot:'#ED1C24' },
    ],
    note: 'Tests: drug safety checks',
    accent: true,
    caseText: '65 year old male, chest pain since morning, diabetic, smoker 20 years, on warfarin and recently prescribed clarithromycin',
  },
  {
    id: 2,
    title: '28F — Fever + Neck Pain',
    badge: { text:'🚨 Critical Warning Signs', color:'#ED1C24', bg:'rgba(237,28,36,0.08)' },
    symptoms: [
      { text:'Headache', dot:'#ED1C24' },
      { text:'Neck Stiffness', dot:'#ED1C24' },
      { text:'Fever', dot:'#ED1C24' },
    ],
    note: 'Tests: red flag detection',
    accent: false,
    caseText: '28 year old female, severe headache, neck stiffness, high fever, light sensitivity. No recent travel.',
  },
  {
    id: 3,
    title: '45M — Medication Risk',
    badge: { text:'⚠ Possible Medication Toxicity', color:'#a2e7ff', bg:'rgba(31,54,81,0.6)' },
    symptoms: [
      { text:'Paracetamol Daily', dot:'#00d4ff' },
      { text:'Heavy Drinker', dot:'#ED1C24' },
    ],
    note: 'Tests: toxicity screening',
    accent: false,
    caseText: '45 year old male, takes paracetamol 1g daily for back pain, drinks heavily (6-8 units/day), noticed yellowing of eyes.',
  },
  {
    id: 4,
    title: '55F — Conflicting Medical Info',
    badge: { text:'⚠ Conflicting Medical Information', color:'#ED1C24', bg:'rgba(237,28,36,0.08)' },
    symptoms: [
      { text:'"No allergies" on record', dot:'#00d4ff' },
      { text:'Mentions amoxicillin reaction', dot:'#ED1C24' },
    ],
    note: 'Tests: history reconciliation',
    accent: false,
    caseText: '55 year old female, presents with sinus infection. Forms say no allergies. Patient mentions she had a reaction to amoxicillin in 2019.',
  },
  {
    id: 5,
    title: '70M — Infection Risk (Possible Sepsis)',
    badge: { text:'🚨 Possible Severe Infection (Sepsis)', color:'#a2e7ff', bg:'rgba(31,54,81,0.6)' },
    symptoms: [
      { text:'Long-term steroids', dot:'#00d4ff' },
      { text:'Fever + Low BP + Confusion', dot:'#ED1C24' },
    ],
    note: 'Tests: vital sign analysis',
    accent: false,
    caseText: '70 year old male, on long-term prednisone for COPD. Now presenting with fever 38.8°C, BP 85/55, confused. Family says he seemed fine yesterday.',
  },
];

export default function DemoCases() {
  const navigate = useNavigate();

  function runCase(caseText) {
    sessionStorage.setItem('medsignal_case', caseText);
    navigate('/analysis');
  }

  return (
    <div style={{ minHeight:'100vh', background:'#050d1a',
      backgroundImage:'radial-gradient(rgba(122,144,176,0.08) 1px, transparent 1px)',
      backgroundSize:'32px 32px' }}>

      <TopNavBar />

      <main style={{ maxWidth:'1440px', margin:'0 auto', padding:'88px 24px 40px' }}>

        {/* Header */}
        <header style={{ borderBottom:'1px solid rgba(122,144,176,0.15)', paddingBottom:'16px', marginBottom:'32px' }}>
          <h1 style={{ fontFamily:"'Space Grotesk',sans-serif", fontWeight:600, fontSize:'32px',
            letterSpacing:'0.02em', color:'#fff' }}>Demo Cases</h1>
          <p style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'13px', color:'var(--text-dim)', marginTop:'6px' }}>
            Realistic emergency scenarios to test critical risk detection.
          </p>
          <p style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'12px', color:'var(--text-dim)',
            opacity:0.65, marginTop:'4px' }}>
            Click any case to see how MedSignal detects risks and recommends actions in real time.
          </p>
        </header>

        {/* Grid */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:'24px' }}>
          {CASES.map((c, i) => (
            <motion.div key={c.id}
              initial={{ opacity:0, y:20 }}
              animate={{ opacity:1, y:0 }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ y:-4, boxShadow:'0 0 20px rgba(0,212,255,0.08)', borderColor:'rgba(0,212,255,0.3)' }}
              style={{
                background:'#0f1e35',
                border:`1px solid rgba(122,144,176,0.12)`,
                borderLeft: c.accent ? '2px solid #00d4ff' : '1px solid rgba(122,144,176,0.12)',
                padding:'20px',
                display:'flex', flexDirection:'column', gap:'16px',
                position:'relative', overflow:'hidden',
                transition:'all 0.25s',
                gridColumn: c.id === 5 ? 'auto' : 'auto',
                cursor:'default',
              }}>

              {/* Ghost number */}
              <div style={{ position:'absolute', top:0, right:0, padding:'8px',
                fontFamily:"'Space Grotesk',sans-serif", fontWeight:600, fontSize:'32px',
                color:'rgba(122,144,176,0.08)', lineHeight:1, pointerEvents:'none' }}>
                {String(c.id).padStart(2,'0')}
              </div>

              {/* Top bar */}
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'8px' }}>
                <span className="label-caps" style={{ color:'var(--text-dim)', marginTop:'2px' }}>Patient Profile</span>
                <span style={{ background:c.badge.bg, color:c.badge.color,
                  border:`1px solid ${c.badge.color}40`, fontFamily:"'JetBrains Mono',monospace",
                  fontWeight:700, fontSize:'10px', letterSpacing:'0.08em', textTransform:'uppercase',
                  padding:'3px 8px', display:'flex', alignItems:'center', gap:'4px',
                  whiteSpace:'nowrap' }}>
                  {c.badge.text}
                </span>
              </div>

              {/* Title + symptoms */}
              <div>
                <h2 style={{ fontFamily:"'Space Grotesk',sans-serif", fontWeight:600, fontSize:'20px',
                  color:'#fff', lineHeight:1.25, marginBottom:'12px' }}>{c.title}</h2>
                <ul style={{ listStyle:'none', display:'flex', flexDirection:'column', gap:'6px' }}>
                  {c.symptoms.map(s => (
                    <li key={s.text} style={{ display:'flex', alignItems:'flex-start', gap:'8px',
                      fontFamily:"'JetBrains Mono',monospace", fontSize:'13px', color:'var(--text-dim)' }}>
                      <span style={{ width:'7px', height:'7px', borderRadius:'50%',
                        background:s.dot, marginTop:'4px', flexShrink:0 }} />
                      {s.text}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer */}
              <div style={{ marginTop:'auto', paddingTop:'16px',
                borderTop:'1px solid rgba(122,144,176,0.1)',
                display:'flex', flexDirection:'column', gap:'10px' }}>
                <p style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:'11px',
                  color:'var(--text-dim)', opacity:0.6 }}>{c.note}</p>
                <button className="btn-primary"
                  onClick={() => runCase(c.caseText)}
                  style={{ width:'100%', padding:'10px', display:'flex',
                    alignItems:'center', justifyContent:'center', gap:'8px' }}>
                  Run This Case →
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
}