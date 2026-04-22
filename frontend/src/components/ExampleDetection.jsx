import React from 'react';

export default function ExampleDetection() {
  return (
    <section className="px-margin py-24 max-w-container-max mx-auto border-b border-surface-container-high/50">
      <div className="mb-8 flex flex-col gap-2">
        <h2 className="font-h2 text-h2 text-on-surface uppercase text-center">Example Detection</h2>
      </div>
      <div className="bg-surface-container-highest/50 border border-surface-container-high p-6 flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-[#ED1C24]"></div>
        <div className="flex-1">
          <div className="font-label-caps text-tertiary-fixed-dim mb-2 uppercase">Input</div>
          <div className="font-data-mono text-on-surface bg-background/50 p-3 rounded-sm border border-surface-container-high">
            Severe chest pain + difference in blood pressure between arms
          </div>
        </div>
        <div className="hidden md:flex text-tertiary-fixed-dim">
          <span className="material-symbols-outlined">arrow_right_alt</span>
        </div>
        <div className="flex-1">
          <div className="font-label-caps text-tertiary-fixed-dim mb-2 uppercase">Output</div>
          <div className="font-data-mono text-[#ED1C24] bg-[#ED1C24]/10 p-3 rounded-sm border border-[#ED1C24]/30 flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">warning</span>
           {/* 🚨  CHANGED: replaced complex diagnosis with intuitive one */}
            🚨 Probable Heart Attack (Acute Coronary Syndrome)
          </div>
        </div>
        <div className="hidden md:flex text-tertiary-fixed-dim">
          <span className="material-symbols-outlined">arrow_right_alt</span>
        </div>
        <div className="flex-1">
          <div className="font-label-caps text-tertiary-fixed-dim mb-2 uppercase">Action</div>
          <div className="font-data-mono text-[#00d4ff] bg-[#00d4ff]/10 p-3 rounded-sm border border-[#00d4ff]/30">
            Immediate CT scan recommended
          </div>
        </div>
      </div>
    </section>
  );
}