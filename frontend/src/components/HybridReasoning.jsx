import React from 'react';

export default function HybridReasoning() {
  const cards = [
    { id: 1, icon: 'hub', title: 'Pattern Engine', desc: 'Medical rules to catch known danger patterns.', color: 'text-on-surface' },
    { id: 2, icon: 'database', title: 'OpenFDA API', desc: 'Checks drug safety and interactions in real time.', color: 'text-secondary-fixed-dim', active: true },
    { id: 3, icon: 'psychiatry', title: 'LLM Reasoning', desc: 'Understands complex or unclear patient descriptions.', color: 'text-on-surface' },
  ];

  return (
    <section className="px-margin py-28 max-w-container-max mx-auto border-b border-surface-container-high/50">
      <div className="mb-12 flex flex-col gap-2">
        <span className="font-label-caps text-label-caps text-tertiary-fixed-dim">02 // ARCHITECTURE</span>
        <h2 className="font-h2 text-h2 text-on-surface uppercase">Hybrid Reasoning Engine</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
        {cards.map((card) => (
          <div key={card.id} className="col-span-1 md:col-span-4 bg-surface-container-highest border border-surface-container-high p-1 relative overflow-hidden group">
            <div className={`absolute inset-0 bg-gradient-to-b ${card.active ? 'from-secondary-fixed-dim/10' : 'from-surface-container-high'} to-transparent opacity-0 group-hover:opacity-100 transition-opacity`}></div>
            <div className={`bg-surface-container-highest border ${card.active ? 'border-secondary-fixed-dim/20' : 'border-outline-variant/20'} p-6 h-full relative z-10 flex flex-col`}>
              <div className={`w-10 h-10 border ${card.active ? 'border-secondary-fixed-dim/50 bg-secondary-fixed-dim/10 text-secondary-fixed-dim' : 'border-tertiary-fixed-dim/30 text-tertiary-fixed-dim'} flex items-center justify-center mb-6`}>
                <span className="material-symbols-outlined text-[20px]">{card.icon}</span>
              </div>
              <h3 className={`font-data-mono text-data-mono ${card.color} uppercase mb-2`}>{card.title}</h3>
              <p className="font-body-main text-body-main text-tertiary-fixed-dim text-sm mt-auto border-t border-surface-container-high pt-4">{card.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}