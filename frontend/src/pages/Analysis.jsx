import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TopNavBar from '../components/TopNavBar';
import Footer from '../components/Footer';
import { track } from '@vercel/analytics';

const DEMO_RESULT = {
    severity: 'CRITICAL',
    headline: 'Possible Heart Attack (Acute Coronary Syndrome)',
    subheadline: 'High-risk cardiac features present — urgent evaluation required',
    dataQuality: 'HIGH',
    dataQualityNote: '(complete vitals + history present)',
    redFlags: [
        'Severe chest pain in high-risk patient (diabetes + smoking).',
        'Symptoms consistent with Acute Coronary Syndrome (heart attack risk).',
    ],
    differential: [
        {
            rank: '01',
            condition: 'Acute Coronary Syndrome (Heart Attack)',
            reasoning: 'chest pain + diabetes + smoking (classic high-risk pattern)',
            probability: 'VERY LIKELY',
            probColor: '#ED1C24',
            border: '#ED1C24'
        },
        {
            rank: '02',
            condition: 'Pulmonary Embolism',
            reasoning: 'chest pain with risk factors',
            probability: 'POSSIBLE',
            probColor: '#f97316',
            border: '#f97316'
        },
        {
            rank: '03',
            condition: 'Gastric / Acid Reflux',
            reasoning: 'chest discomfort alternative cause',
            probability: 'LESS LIKELY',
            probColor: '#fbbf24',
            border: '#fbbf24'
        },
    ],
    actions: [
        'Immediate ECG and cardiac monitoring.',
        'Check troponin levels urgently.',
        'Do not delay cardiology evaluation.',
    ],
    missing: ['medication history', 'symptom duration'],
};

const AGENTS = [
    { id: 'intake', label: 'Intake Processor', icon: 'input', doneFirst: true },
    { id: 'ddx', label: 'Differential (DDx)', icon: 'memory', pulse: 'ddx' },
    { id: 'redflag', label: 'Red Flag Scan', icon: 'radar', pulse: 'redflag' },
    { id: 'consist', label: 'Data Consistency', icon: 'fact_check' },
    { id: 'summary', label: 'Report Synthesis', icon: 'summarize' },
];

function AgentRow({ agent, status }) {
    const isCompleted = status === 'COMPLETED';
    const isProcessing = status === 'PROCESSING' || status === 'ANALYZING';
    const isIdle = status === 'IDLE';
    const color = isCompleted ? '#3cd7ff' : isProcessing && agent.pulse === 'redflag' ? '#ff544b'
        : isProcessing ? '#3cd7ff' : 'rgba(122,144,176,0.4)';
    const pulseCss = isProcessing ? (agent.pulse === 'redflag' ? { animation: 'redflag-pulse 2s infinite' } : { animation: 'ddx-pulse 2s infinite' }) : {};

    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            fontFamily: "'JetBrains Mono',monospace", fontSize: '13px',
            padding: isProcessing ? '8px' : '4px 8px',
            margin: isProcessing ? '0 -8px' : '0 0',
            background: isProcessing && agent.pulse === 'redflag' ? 'rgba(255,84,75,0.06)'
                : isProcessing ? 'rgba(60,215,255,0.06)' : 'transparent',
            border: isProcessing ? `1px solid ${color}22` : 'none',
            opacity: isIdle ? 0.45 : 1,
            ...pulseCss,
        }}>
            <div style={{
                width: '24px', height: '24px', borderRadius: '50%', border: `1px solid ${color}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', color,
                boxShadow: isProcessing ? `0 0 8px ${color}` : 'none'
            }}>
                <span className="material-symbols-outlined" style={{
                    fontSize: '13px',
                    animation: isProcessing ? 'spin 1.5s linear infinite' : 'none'
                }}>
                    {isCompleted ? 'check' : isIdle ? 'pending' : agent.icon}
                </span>
            </div>
            <span style={{ flex: 1, color: isIdle ? 'var(--text-dim)' : isProcessing && agent.pulse === 'redflag' ? '#ff544b' : isProcessing ? '#3cd7ff' : 'var(--text)' }}>
                {agent.label}
            </span>
            <span className="label-caps" style={{ color, animation: isProcessing ? 'pulse-opacity 1.5s ease infinite' : 'none' }}>
                {status}
            </span>
        </div>
    );
}

function transformApiResponse(data) {
    if (!data) return null;

    const probColor = { HIGH: '#ED1C24', MEDIUM: '#f97316', LOW: '#fbbf24' };
    const topCondition = data.differential?.[0]?.condition || 'Unknown';
    const sev = data.severity || 'UNKNOWN';

    return {
        severity: sev,
        headline: topCondition,
        subheadline: sev === 'CRITICAL'
            ? 'Critical risk detected — urgent evaluation required'
            : sev === 'HIGH'
                ? 'High-risk features present — prompt evaluation needed'
                : 'Risk factors identified — clinical review recommended',
        dataQuality: data.data_quality || 'UNKNOWN',
        dataQualityNote: data.consistency_notes?.length
            ? `(${data.consistency_notes.length} consistency issue(s) found)`
            : '(based on available data)',
        redFlags: data.red_flags || [], // backend sends snake_case
        differential: data.differential?.map((d, i) => ({
            rank: String(i + 1).padStart(2, '0'),
            condition: d.condition,
            reasoning: d.reasoning,
            probability: d.probability,
            probColor: probColor[d.probability] || '#fbbf24',
            border: probColor[d.probability] || '#fbbf24',
        })) || [],
        actions: data.recommendations || [],
        missing: data.consistency_notes?.length
            ? data.consistency_notes
            : ['No major data gaps detected'],
        requires_verification: data.requires_verification || false,
    };
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
        intake: 'IDLE', ddx: 'IDLE', redflag: 'IDLE', consist: 'IDLE', summary: 'IDLE'
    });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    async function runAnalysis() {
        if (!caseText.trim() || loading) return;
        setResult(null);
        setLoading(true);
        setAgentStatuses({ intake: 'PROCESSING', ddx: 'IDLE', redflag: 'IDLE', consist: 'IDLE', summary: 'IDLE' });

        // Analytics - safe metadata only
        track('analyze_started', { case_length: caseText.length });
        const startTime = Date.now();

        try {
            const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
            const response = await fetch(`${API}/analyze/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ case: caseText }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const events = buffer.split('\n\n');
                buffer = events.pop() || '';

                for (const event of events) {
                    if (!event.trim()) continue;
                    const eventType = event.match(/event: (\w+)/)?.[1];
                    const dataMatch = event.match(/data: (.+)/);
                    if (!dataMatch) continue;
                    const data = JSON.parse(dataMatch[1]);

                    if (eventType === 'status') {
                        setAgentStatuses(prev => ({
                            ...prev,
                            [data.agent]: data.status === 'PROCESSING' ? 'PROCESSING' : 'COMPLETED'
                        }));
                    }
                    if (eventType === 'result') {
                        if (data) {
                            setResult(transformApiResponse(data));
                        }
                        const duration = Date.now() - startTime;
                        track('analyze_completed', {
                            severity: data.severity,
                            red_flag_count: data.red_flags?.length || 0,
                            data_quality: data.data_quality,
                            duration_ms: duration,
                        });
                        setResult(transformApiResponse(data));
                    }
                }
            }
        } catch (err) {
            track('analyze_failed');
            console.error("Stream failed:", err);
            setResult(null);
            setAgentStatuses({ intake: 'IDLE', ddx: 'IDLE', redflag: 'IDLE', consist: 'IDLE', summary: 'IDLE' });
        } finally {
            setLoading(false);
        }
    }

    const r = (result && result.severity) ? result : DEMO_RESULT;
    console.log("FINAL R:", r);
    const severityConfig = {
        CRITICAL: { color: '#ffb4ab', border: 'rgba(255,180,171,0.6)', shadow: 'rgba(255,180,171,0.1)', label: 'CRITICAL' },
        HIGH: { color: '#f97316', border: 'rgba(249,115,22,0.6)', shadow: 'rgba(249,115,22,0.1)', label: 'HIGH RISK' },
        MEDIUM: { color: '#fbbf24', border: 'rgba(251,191,36,0.6)', shadow: 'rgba(251,191,36,0.1)', label: 'MODERATE RISK' },
        LOW: { color: '#22c55e', border: 'rgba(34,197,94,0.6)', shadow: 'rgba(34,197,94,0.1)', label: 'LOW RISK' },
    };
    const sev = severityConfig[r.severity] || severityConfig.LOW;
    return (
        <div style={{ minHeight: '100vh', position: 'relative' }}>
            <TopNavBar />
            <div style={{
                position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
                backgroundImage: 'radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px)',
                backgroundSize: '32px 32px'
            }} />

            <main style={{
                position: 'relative', zIndex: 1, maxWidth: '1440px', margin: '0 auto',
                padding: '88px 24px 24px', display: 'grid',
                gridTemplateColumns: '400px 1fr', gap: '16px', minHeight: '100vh'
            }}>

                {/* LEFT COLUMN */}
                <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

                    {/* Input panel */}
                    <div className="panel" style={{ padding: '16px', borderLeft: '2px solid #00d2fd' }}>
                        <div className="label-caps" style={{
                            color: '#00d2fd', marginBottom: '16px',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                        }}>
                            <span>Patient Input</span>
                            <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#00d2fd' }}>input</span>
                        </div>
                        <textarea
                            value={caseText}
                            onChange={e => setCaseText(e.target.value)}
                            placeholder="Enter clinical notes, vitals, or patient history here..."
                            style={{
                                width: '100%', height: '180px', background: 'rgba(0,20,42,0.8)',
                                border: 'none', borderBottom: '1px solid rgba(31,54,81,0.8)',
                                color: 'var(--text)', fontFamily: "'JetBrains Mono',monospace",
                                fontSize: '13px', padding: '8px', resize: 'none', outline: 'none',
                                lineHeight: 1.5,
                            }}
                        />
                        <button className="btn-primary"
                            onClick={runAnalysis}
                            disabled={loading}
                            style={{
                                width: '100%', marginTop: '12px', padding: '12px',
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                                opacity: loading ? 0.7 : 1, cursor: loading ? 'wait' : 'pointer'
                            }}>
                            {loading ? 'ANALYZING...' : 'ANALYZE'}
                            <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>arrow_forward</span>
                        </button>
                    </div>

                    {/* Agent Status */}
                    <div className="panel" style={{ padding: '16px' }}>
                        <div className="label-caps" style={{ color: '#8991a2', marginBottom: '16px' }}>Agent Status</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {AGENTS.map(a => (
                                <AgentRow key={a.id} agent={a} status={agentStatuses[a.id]} />
                            ))}
                        </div>
                    </div>
                </section>

                {/* RIGHT COLUMN */}
                <section style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

                    {/* Header */}
                    <AnimatePresence>
                        {result && (
                            <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}
                                style={{
                                    display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px',
                                    borderBottom: '1px solid rgba(31,54,81,0.8)', paddingBottom: '16px'
                                }}>
                                <div style={{
                                    border: `1px solid ${sev.border}`, padding: '16px 20px',
                                    boxShadow: `0 0 15px ${sev.shadow}`, flex: 1
                                }}>
                                    <div style={{
                                        fontFamily: "'Space Grotesk',sans-serif", fontWeight: 600, fontSize: '22px',
                                        color: sev.color, display: 'flex', alignItems: 'center', gap: '8px'
                                    }}>
                                        {sev.label}: {r.headline}
                                    </div>
                                    <div style={{
                                        fontFamily: "'Space Grotesk',sans-serif", fontSize: '16px',
                                        color: sev.color, opacity: 0.9, marginTop: '4px'
                                    }}>
                                        {r.subheadline}
                                    </div>
                                </div>
                                <div style={{
                                    border: '1px solid rgba(60,215,255,0.15)', padding: '8px 12px',
                                    display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', opacity: 0.75
                                }}>
                                    <div className="label-caps" style={{ color: '#3cd7ff' }}>DATA QUALITY: {r.dataQuality}</div>
                                    <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: '#8991a2' }}>{r.dataQualityNote}</div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Red Flags */}
                    <div className="panel" style={{ padding: '16px', borderLeft: '2px solid #ED1C24' }}>
                        <div className="label-caps" style={{
                            color: '#ED1C24', marginBottom: '16px',
                            display: 'flex', alignItems: 'center', gap: '6px'
                        }}>
                            <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>flag</span>
                            Red Flags
                        </div>
                        
                        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {(r.red_flags || r.redFlags)?.map((f, i) => (
                                <li key={i} style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '12px',
                                    background: 'rgba(31,54,81,0.25)',
                                    padding: '12px',
                                    border: '1px solid rgba(31,54,81,0.5)'
                                }}>
                                    <span style={{ color: '#ED1C24', fontWeight: 700, fontSize: '18px', lineHeight: 1 }}>—</span>
                                    <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '13px', color: 'var(--text)' }}>
                                        {typeof f === 'string' ? f : f.flag}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* DDx Table */}
                    <div className="panel" style={{ padding: '16px' }}>
                        <div className="label-caps" style={{
                            color: '#8991a2', marginBottom: '16px',
                            display: 'flex', alignItems: 'center', gap: '6px'
                        }}>
                            <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>format_list_numbered</span>
                            Differential Diagnosis (Ranked)
                        </div>
                        <table style={{
                            width: '100%',
                            tableLayout: 'fixed', // CHANGED: forces consistent column widths
                            borderCollapse: 'separate',
                            borderSpacing: '0 12px',
                            fontFamily: "'JetBrains Mono',monospace",
                            fontSize: '13px'
                        }}>
                            <thead>
                                <tr>
                                    <th style={{ width: '8%', textAlign: 'left', padding: '4px 8px', color: '#8991a2' }}>RANK</th>
                                    <th style={{ width: '52%', textAlign: 'left', padding: '4px 8px', color: '#8991a2' }}>Condition & Reasoning</th>
                                    <th style={{ width: '20%', textAlign: 'right', padding: '4px 8px', color: '#8991a2' }}>Probability</th>
                                    <th style={{ width: '20%', textAlign: 'right', padding: '4px 8px', color: '#8991a2' }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {r.differential?.map(d => (
                                    <tr key={d.rank} style={{
                                        background: 'rgba(31,54,81,0.12)',
                                        verticalAlign: 'middle' // CHANGED: fixes uneven row alignment
                                    }}>
                                        <td style={{
                                            width: '8%',
                                            padding: '16px 12px',
                                            borderLeft: `4px solid ${d.border}`,
                                            fontWeight: 700,
                                            color: d.border,
                                            verticalAlign: 'middle' // CHANGED
                                        }}>
                                            {d.rank}
                                        </td>
                                        <td style={{
                                            width: '52%',
                                            padding: '16px 12px',
                                            verticalAlign: 'middle'
                                        }}>
                                            <div style={{
                                                fontWeight: 700,
                                                fontSize: '14px',
                                                color: 'var(--text)',
                                                marginBottom: '4px'
                                            }}>
                                                {d.condition}
                                            </div>

                                            <div style={{
                                                fontSize: '11px',
                                                color: '#8991a2',
                                                lineHeight: 1.5
                                            }}>
                                                → {d.reasoning.replace(/\w+:/g, '').replace(/\+/g, '·').trim()}
                                            </div>
                                        </td>
                                        <td style={{
                                            width: '20%',
                                            padding: '16px 12px',
                                            textAlign: 'right',
                                            verticalAlign: 'middle'
                                        }}>
                                            <div style={{
                                                fontWeight: 700,
                                                color: d.probColor
                                            }}>
                                                {d.probability}
                                            </div>
                                        </td>
                                        <td style={{
                                            width: '20%',
                                            padding: '16px 12px',
                                            textAlign: 'right',
                                            verticalAlign: 'middle'
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                                {d.rank === '01' ? (
                                                    <button style={{
                                                        background: '#00d2fd',
                                                        color: '#000f22',
                                                        fontFamily: "'JetBrains Mono',monospace",
                                                        fontWeight: 700,
                                                        fontSize: '10px',
                                                        letterSpacing: '0.1em',
                                                        textTransform: 'uppercase',
                                                        padding: '6px 12px',
                                                        border: 'none',
                                                        cursor: 'pointer'
                                                    }}>
                                                        VIEW PROTOCOL
                                                    </button>
                                                ) : (
                                                    <button style={{
                                                        background: 'transparent',
                                                        border: '1px solid rgba(31,54,81,0.8)',
                                                        color: '#8991a2',
                                                        fontFamily: "'JetBrains Mono',monospace",
                                                        fontSize: '10px',
                                                        letterSpacing: '0.08em',
                                                        textTransform: 'uppercase',
                                                        padding: '4px 10px',
                                                        cursor: 'pointer'
                                                    }}>
                                                        Why this diagnosis
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Actions + Missing */}
                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
                        <div className="panel" style={{ padding: '16px' }}>
                            <div className="label-caps" style={{
                                color: '#00d2fd', marginBottom: '16px',
                                display: 'flex', alignItems: 'center', gap: '6px'
                            }}>
                                <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>play_circle</span>
                                Recommended Actions
                            </div>
                            <div style={{
                                display: 'flex', flexDirection: 'column', gap: '12px',
                                fontFamily: "'JetBrains Mono',monospace", fontSize: '13px'
                            }}>
                                {r.actions?.map((a, i) => (
                                    <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                        <span style={{
                                            border: '1px solid rgba(0,210,253,0.5)', color: '#00d2fd',
                                            padding: '1px 6px', fontSize: '10px', fontWeight: 700, marginTop: '1px', flexShrink: 0
                                        }}>
                                            {String(i + 1).padStart(2, '0')}
                                        </span>
                                        <span style={{ color: 'var(--text)' }}>{a}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="panel" style={{ padding: '16px', borderLeft: '2px solid #fbbf24', opacity: 0.8 }}>
                            <div className="label-caps" style={{
                                color: '#fbbf24', marginBottom: '12px', fontSize: '10px',
                                display: 'flex', alignItems: 'center', gap: '4px'
                            }}>
                                <span className="material-symbols-outlined" style={{ fontSize: '11px' }}>help_outline</span>
                                Missing Information
                            </div>
                            <div style={{
                                fontFamily: "'JetBrains Mono',monospace", fontSize: '12px',
                                color: 'var(--text)', display: 'flex', flexDirection: 'column', gap: '4px'
                            }}>
                                {r.missing?.map(m => <div key={m}>— {m}</div>)}
                            </div>
                        </div>
                    </div>

                    {/* Disclaimer */}
                    <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px',
                        paddingTop: '16px', borderTop: '1px solid rgba(31,54,81,0.8)'
                    }}>
                        <p style={{
                            fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'rgba(138,145,162,0.5)',
                            textTransform: 'uppercase', lineHeight: 1.6, maxWidth: '520px'
                        }}>
                            SYSTEM GENERATED ANALYSIS. AI INFERENCES DO NOT CONSTITUTE FINAL MEDICAL ADVICE.
                            CLINICAL CORRELATION AND PHYSICIAN JUDGMENT ARE REQUIRED BEFORE INITIATING TREATMENT PROTOCOLS.
                        </p>
                        <button style={{
                            flexShrink: 0, background: 'transparent', border: '1px solid #8991a2',
                            color: '#8991a2', fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: '10px',
                            letterSpacing: '0.1em', textTransform: 'uppercase', padding: '8px 16px', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: '6px', transition: 'text-shadow 0.2s'
                        }}
                            onMouseEnter={e => e.currentTarget.style.textShadow = '0 0 8px rgba(188,199,217,0.9)'}
                            onMouseLeave={e => e.currentTarget.style.textShadow = 'none'}>
                            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>download</span>
                            Export Report
                        </button>
                    </div>
                </section>
            </main>

            <Footer />
        </div>
    );
}