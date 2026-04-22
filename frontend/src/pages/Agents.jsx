import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TopNavBar from '../components/TopNavBar';
import Footer from '../components/Footer';

// ─── Agent definitions ───────────────────────────────────────────────────────
const AGENTS = [
  {
    id: 'intake',
    label: 'Intake Processor',
    role: 'Clinical Intake Specialist',
    icon: 'input',
    color: '#3cd7ff',
    accentColor: 'rgba(60,215,255,0.15)',
    borderColor: 'rgba(60,215,255,0.4)',
    capability: 'Parses messy free text into structured JSON. Flags missing fields. Never invents data.',
    model: 'Llama 3 · AMD MI300X',
    metrics: { processed: 1284, avgMs: 312, accuracy: '99.2%' },
    logs: [
      '> Parsing patient input...',
      '> Extracted: age=65, sex=M, symptoms=[chest_pain, dyspnea]',
      '> Flagged: medication_name=UNKNOWN',
      '> Structured JSON ready → parallel agents',
    ],
  },
  {
    id: 'ddx',
    label: 'Differential (DDx)',
    role: 'Differential Diagnosis Expert',
    icon: 'rule',
    color: '#a2e7ff',
    accentColor: 'rgba(162,231,255,0.1)',
    borderColor: 'rgba(162,231,255,0.3)',
    capability: 'Generates ranked conditions by probability and severity from structured input.',
    model: 'Llama 3 · AMD MI300X',
    metrics: { processed: 1284, avgMs: 890, accuracy: '94.7%' },
    logs: [
      '> Analyzing symptom cluster...',
      '> Match: ACS pattern — confidence HIGH',
      '> Match: PE — confidence MODERATE',
      '> Ranked DDx list generated [5 conditions]',
    ],
  },
  {
    id: 'redflag',
    label: 'Red Flag Scanner',
    role: 'Emergency Medicine Specialist',
    icon: 'warning',
    color: '#ED1C24',
    accentColor: 'rgba(237,28,36,0.1)',
    borderColor: 'rgba(237,28,36,0.5)',
    capability: 'Hybrid: 7 hard clinical rules + LLM reasoning + live OpenFDA API grounding.',
    model: 'Llama 3 + OpenFDA · AMD MI300X',
    metrics: { processed: 1284, avgMs: 1240, accuracy: '98.1%' },
    logs: [
      '> Running 7 hard clinical rules...',
      '> RULE HIT: chest_pain + diabetes + age>50 + smoking → CRITICAL',
      '> OpenFDA query: warfarin + clarithromycin...',
      '> FDA CONFIRMED: HIGH bleeding risk interaction',
    ],
  },
  {
    id: 'consistency',
    label: 'Consistency Agent',
    role: 'Case Coherence Checker',
    icon: 'fact_check',
    color: '#bec7d9',
    accentColor: 'rgba(190,199,217,0.08)',
    borderColor: 'rgba(190,199,217,0.25)',
    capability: 'Detects contradictions — stated vs implied history, inconsistent symptom patterns.',
    model: 'Llama 3 · AMD MI300X',
    metrics: { processed: 1284, avgMs: 670, accuracy: '96.3%' },
    logs: [
      '> Cross-referencing stated history...',
      '> Checking: "no allergies" vs drug reactions...',
      '> CONTRADICTION DETECTED: amoxicillin 2019',
      '> Flagging for clinical review',
    ],
  },
  {
    id: 'summary',
    label: 'Report Synthesis',
    role: 'Clinical Report Writer',
    icon: 'summarize',
    color: '#3cd7ff',
    accentColor: 'rgba(60,215,255,0.1)',
    borderColor: 'rgba(60,215,255,0.35)',
    capability: 'Assembles structured output with severity ratings and action recommendations.',
    model: 'Llama 3 · AMD MI300X',
    metrics: { processed: 1284, avgMs: 420, accuracy: '99.8%' },
    logs: [
      '> Collecting agent outputs...',
      '> Ranking severity: CRITICAL',
      '> Generating recommended actions [3]',
      '> Report ready — disclaimer appended',
    ],
  },
];

// ─── Animated log terminal ────────────────────────────────────────────────────
function LogTerminal({ logs, active }) {
  const [visible, setVisible] = useState([]);
  const [idx, setIdx] = useState(0);
  const ref = useRef();

  useEffect(() => {
    if (!active) { setVisible([]); setIdx(0); return; }
    const t = setInterval(() => {
      setIdx(i => {
        if (i >= logs.length) { clearInterval(t); return i; }
        setVisible(v => [...v, logs[i]]);
        return i + 1;
      });
    }, 600);
    return () => clearInterval(t);
  }, [active, logs]);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [visible]);

  return (
    <div ref={ref} style={{
      background: 'rgba(0,15,34,0.8)', border: '1px solid rgba(122,144,176,0.1)',
      padding: '10px 12px', height: '90px', overflowY: 'auto',
      fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', lineHeight: 1.6,
    }}>
      {visible.map((l, i) => (
        <div key={i} style={{ color: l.includes('HIT') || l.includes('CONFIRMED') || l.includes('DETECTED') ? '#ED1C24' : l.includes('>') ? '#3cd7ff' : '#7a90b0' }}>
          {l}
        </div>
      ))}
      {active && idx < logs.length && (
        <span style={{ color: '#3cd7ff', animation: 'pulse-opacity 1s ease infinite' }}>▌</span>
      )}
    </div>
  );
}

// ─── Metric badge ─────────────────────────────────────────────────────────────
function MetricBadge({ label, value, color }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', alignItems: 'center' }}>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: '16px', color }}>
        {value}
      </div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', letterSpacing: '0.1em',
        textTransform: 'uppercase', color: '#7a90b0' }}>
        {label}
      </div>
    </div>
  );
}

// ─── Single agent card ────────────────────────────────────────────────────────
function AgentCard({ agent, index, activeId, onActivate }) {
  const isActive = activeId === agent.id;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      onClick={() => onActivate(isActive ? null : agent.id)}
      style={{
        background: isActive ? agent.accentColor : 'rgba(15,30,53,0.8)',
        border: `1px solid ${isActive ? agent.borderColor : 'rgba(122,144,176,0.12)'}`,
        borderLeft: `2px solid ${isActive ? agent.color : 'rgba(122,144,176,0.2)'}`,
        padding: '20px',
        cursor: 'pointer',
        transition: 'all 0.25s',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: isActive ? `0 0 24px ${agent.accentColor}` : 'none',
      }}
    >
      {/* Active scan line */}
      {isActive && (
        <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
          <div style={{ position: 'absolute', left: 0, width: '100%', height: '1px',
            background: `linear-gradient(90deg, transparent, ${agent.color}60, transparent)`,
            animation: 'scan 3s linear infinite' }} />
        </div>
      )}

      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '50%',
            border: `2px solid ${agent.color}`,
            background: `${agent.accentColor}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: agent.color,
            boxShadow: isActive ? `0 0 14px ${agent.color}55` : 'none',
            transition: 'box-shadow 0.3s',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>{agent.icon}</span>
          </div>
          <div>
            <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 600, fontSize: '15px',
              color: '#fff', letterSpacing: '0.01em' }}>{agent.label}</div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px',
              color: '#7a90b0', letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: '2px' }}>
              {agent.role}
            </div>
          </div>
        </div>

        {/* Status pill */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '5px',
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: '9px',
          letterSpacing: '0.1em', textTransform: 'uppercase',
          color: isActive ? agent.color : '#3cd7ff',
          border: `1px solid ${isActive ? agent.borderColor : 'rgba(60,215,255,0.3)'}`,
          padding: '3px 8px', background: isActive ? agent.accentColor : 'rgba(60,215,255,0.06)',
        }}>
          <span style={{ width: '5px', height: '5px', borderRadius: '50%',
            background: isActive ? agent.color : '#3cd7ff',
            animation: 'pulse-opacity 2s ease infinite' }} />
          {isActive ? 'ACTIVE' : 'STANDBY'}
        </div>
      </div>

      {/* Capability */}
      <p style={{ fontFamily: "'Inter',sans-serif", fontSize: '13px', color: '#bec7d9',
        lineHeight: 1.55, marginBottom: '16px' }}>
        {agent.capability}
      </p>

      {/* Metrics row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)',
        borderTop: '1px solid rgba(122,144,176,0.1)', paddingTop: '14px', marginBottom: '14px' }}>
        <MetricBadge label="Cases" value={agent.metrics.processed.toLocaleString()} color={agent.color} />
        <MetricBadge label="Avg Latency" value={`${agent.metrics.avgMs}ms`} color="#bec7d9" />
        <MetricBadge label="Accuracy" value={agent.metrics.accuracy} color="#22c55e" />
      </div>

      {/* Model tag */}
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px',
        color: '#7a90b0', letterSpacing: '0.06em', marginBottom: '10px' }}>
        <span style={{ color: 'rgba(122,144,176,0.4)', marginRight: '6px' }}>MODEL //</span>
        {agent.model}
      </div>

      {/* Log terminal — shown when active */}
      <AnimatePresence>
        {isActive && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}>
            <LogTerminal logs={agent.logs} active={isActive} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Click hint */}
      {!isActive && (
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'rgba(122,144,176,0.4)',
          letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: '4px' }}>
          CLICK TO ACTIVATE →
        </div>
      )}
    </motion.div>
  );
}

// ─── Parallel execution diagram ───────────────────────────────────────────────
function ParallelDiagram() {
  const parallel = ['ddx', 'redflag', 'consistency'];

  return (
    <div style={{ background: 'rgba(6,32,59,0.6)', border: '1px solid rgba(122,144,176,0.12)',
      padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '20px' }}>
        <div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px',
            color: '#7a90b0', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
            EXECUTION MODEL
          </div>
          <h2 style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 600, fontSize: '18px',
            color: '#fff', letterSpacing: '0.02em', textTransform: 'uppercase' }}>
            Parallel Agent Pipeline
          </h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px',
          fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', fontWeight: 700,
          letterSpacing: '0.1em', color: '#ED1C24',
          border: '1px solid rgba(237,28,36,0.3)', padding: '6px 12px',
          background: 'rgba(237,28,36,0.06)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>memory</span>
          AMD INSTINCT MI300X
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto 1fr', alignItems: 'center', gap: '8px' }}>

        {/* Intake */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '50%',
              border: '2px solid #3cd7ff', background: 'rgba(60,215,255,0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#3cd7ff', boxShadow: '0 0 12px rgba(60,215,255,0.3)' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>input</span>
            </div>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px',
              fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#3cd7ff' }}>
              INTAKE
            </span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px',
              color: '#22c55e' }}>~312ms</span>
          </div>
        </div>

        {/* Arrow + fork */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px', color: '#3cd7ff', opacity: 0.5 }}>
          <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>arrow_forward</span>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '8px',
            color: '#7a90b0', letterSpacing: '0.08em' }}>FORK</span>
        </div>

        {/* Parallel agents */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px',
          border: '1px dashed rgba(60,215,255,0.2)', padding: '12px',
          background: 'rgba(60,215,255,0.03)', position: 'relative' }}>
          <div style={{ position: 'absolute', top: '-9px', left: '12px',
            fontFamily: "'JetBrains Mono',monospace", fontSize: '8px', fontWeight: 700,
            letterSpacing: '0.1em', color: '#3cd7ff', background: '#050d1a', padding: '0 4px' }}>
            PARALLEL ⚡
          </div>
          {[
            { id:'ddx', label:'DDx', icon:'rule', color:'#a2e7ff', ms:'890ms' },
            { id:'redflag', label:'Red Flag', icon:'warning', color:'#ED1C24', ms:'1240ms' },
            { id:'consist', label:'Consistency', icon:'fact_check', color:'#bec7d9', ms:'670ms' },
          ].map(a => (
            <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%',
                border: `1px solid ${a.color}`, background: `${a.color}15`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: a.color }}>
                <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>{a.icon}</span>
              </div>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px',
                color: a.color, fontWeight: 700, flex: 1 }}>{a.label}</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: '#22c55e' }}>{a.ms}</span>
            </div>
          ))}
        </div>

        {/* Arrow + join */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px', color: '#3cd7ff', opacity: 0.5 }}>
          <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>arrow_forward</span>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '8px',
            color: '#7a90b0', letterSpacing: '0.08em' }}>JOIN</span>
        </div>

        {/* Summary */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '50%',
              border: '2px solid #3cd7ff', background: 'rgba(60,215,255,0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#3cd7ff', boxShadow: '0 0 12px rgba(60,215,255,0.3)' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>summarize</span>
            </div>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px',
              fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#3cd7ff' }}>
              SUMMARY
            </span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: '#22c55e' }}>~420ms</span>
          </div>
        </div>
      </div>

      {/* Total latency bar */}
      <div style={{ marginTop: '20px', borderTop: '1px solid rgba(122,144,176,0.1)', paddingTop: '14px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', color: '#7a90b0' }}>
          TOTAL WALL TIME (parallel) vs SEQUENTIAL
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
              fontSize: '18px', color: '#22c55e' }}>~1.97s</div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px',
              color: '#22c55e', letterSpacing: '0.08em' }}>PARALLEL (AMD)</div>
          </div>
          <div style={{ color: 'rgba(122,144,176,0.3)', fontSize: '20px' }}>vs</div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
              fontSize: '18px', color: '#7a90b0', textDecoration: 'line-through' }}>~4.53s</div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9px',
              color: '#7a90b0', letterSpacing: '0.08em' }}>SEQUENTIAL</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Agents() {
  const [activeId, setActiveId] = useState(null);

  return (
    <div style={{ minHeight: '100vh', background: '#050d1a',
      backgroundImage: 'radial-gradient(rgba(122,144,176,0.08) 1px, transparent 1px)',
      backgroundSize: '32px 32px' }}>

      <TopNavBar />

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '88px 24px 40px' }}>

        {/* Page header */}
        <header style={{ borderBottom: '1px solid rgba(122,144,176,0.15)',
          paddingBottom: '20px', marginBottom: '28px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px',
              color: '#7a90b0', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '6px' }}>
              04 // AGENTS
            </div>
            <h1 style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 600,
              fontSize: '32px', letterSpacing: '0.02em', color: '#fff' }}>
              Agent Network
            </h1>
            <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '13px',
              color: '#7a90b0', marginTop: '6px' }}>
              5 specialized agents. One engine. Click any agent to activate its terminal.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px',
            fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', fontWeight: 700,
            letterSpacing: '0.1em', color: '#3cd7ff' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%',
              background: '#3cd7ff', animation: 'pulse-opacity 2s ease infinite',
              boxShadow: '0 0 6px #3cd7ff' }} />
            ALL AGENTS ONLINE
          </div>
        </header>

        {/* Parallel execution diagram */}
        <ParallelDiagram />

        {/* Agent cards grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          {AGENTS.map((agent, i) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              index={i}
              activeId={activeId}
              onActivate={setActiveId}
            />
          ))}
        </div>

        {/* Footer note */}
        <div style={{ marginTop: '32px', padding: '16px',
          border: '1px solid rgba(122,144,176,0.1)', background: 'rgba(6,32,59,0.4)',
          display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#7a90b0' }}>info</span>
          <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', color: '#7a90b0',
            letterSpacing: '0.04em', lineHeight: 1.6 }}>
            All 5 agents run on the same model — Llama 3 via AMD Developer Cloud. What differentiates each
            agent is its role, goal, and task prompt. One engine, five specialists. Parallel execution
            on AMD Instinct MI300X reduces total wall time by ~56% vs sequential inference.
          </p>
        </div>

      </main>

      <Footer />
    </div>
  );
}