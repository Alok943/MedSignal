import React from 'react';

export default function ComparisonTable() {
  const rows = [
    { label: 'Architecture', std: 'Single LLM', med: 'Multi-Agent System (Parallel Analysis)' },
    { label: 'Hallucination Risk', std: <span className="text-primary-container">High (Generative)</span>, med: <span className="text-secondary-fixed-dim">Zero-Tolerance (Medical Rule Verification)</span>, highlight: true },
    { label: 'Data Verification', std: 'Static Training', med: 'Live Drug Interaction Checks' },
    { label: 'Hardware', std: 'Generic Cloud', med: <span className="text-secondary-fixed-dim font-bold tracking-widest">High-Speed AMD Performance</span>, highlight: true },
  ];

  return (
    <section className="px-margin py-28 max-w-container-max mx-auto mb-16">
      <div className="mb-12 flex flex-col gap-2">
        <span className="font-label-caps text-label-caps text-tertiary-fixed-dim">03 // METRICS</span>
        <h2 className="font-h2 text-h2 text-on-surface uppercase">Why MedSignal is Safer Than Standard AI</h2>
      </div>
      <div className="border border-surface-container-high bg-surface-container font-data-mono text-data-mono text-sm">
        {/* Header */}
        <div className="grid grid-cols-12 border-b border-surface-container-high bg-surface-container-highest/50 text-tertiary-fixed-dim uppercase py-3 px-4">
          <div className="col-span-4">Parameter</div>
          <div className="col-span-4 border-l border-surface-container-high pl-4">Standard AI</div>
          <div className="col-span-4 border-l border-surface-container-high pl-4 text-secondary-fixed-dim flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px]">shield</span>
            MedSignal
          </div>
        </div>
        {/* Rows */}
        {rows.map((row, idx) => (
          <div key={idx} className={`grid grid-cols-12 py-4 px-4 hover:bg-surface-container-highest/30 transition-colors ${row.highlight ? 'bg-surface-container-highest/10' : ''} ${idx !== rows.length - 1 ? 'border-b border-surface-container-high' : ''}`}>
            <div className="col-span-4 text-on-surface">{row.label}</div>
            <div className="col-span-4 border-l border-surface-container-high pl-4 text-tertiary-fixed-dim">{row.std}</div>
            <div className="col-span-4 border-l border-surface-container-high pl-4 text-on-surface">{row.med}</div>
          </div>
        ))}
      </div>
    </section>
  );
}