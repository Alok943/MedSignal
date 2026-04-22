import React from 'react';

export default function ProtocolSequence() {
  return (
    <section className="px-margin py-28 max-w-container-max mx-auto border-b border-surface-container-high/50">
      <div className="mb-12 flex flex-col gap-2">
        <span className="font-label-caps text-label-caps text-tertiary-fixed-dim">01 // PROCESS</span>
        <h2 className="font-h2 text-h2 text-on-surface uppercase">Protocol Sequence</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
        {/* Step 1 */}
        <div className="bg-surface-container-highest border border-surface-container-high relative p-6 h-full flex flex-col">
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-secondary-fixed-dim/50 to-transparent"></div>
          <div className="font-label-caps text-label-caps text-tertiary-fixed-dim mb-6 bg-background/50 inline-block px-2 py-1 border border-outline-variant/30 w-fit">SEQ_01</div>
          <h3 className="font-body-strong text-body-strong text-on-surface mb-2">Paste symptoms, notes, or patient details.</h3>
        </div>
        {/* Step 2 */}
        <div className="bg-surface-container-highest border-l-2 border-secondary-fixed-dim relative p-6 h-full flex flex-col shadow-[-12px_0_24px_-12px_rgba(60,215,255,0.15)]">
          <div className="font-label-caps text-label-caps text-secondary-fixed-dim mb-6 bg-secondary-fixed-dim/10 inline-block px-2 py-1 border border-secondary-fixed-dim/30 w-fit flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px]">memory</span>
            SEQ_02_ACTIVE
          </div>
          <h3 className="font-body-strong text-body-strong text-on-surface mb-2">Parallel analysis by multiple agents.</h3>
        </div>
        {/* Step 3 */}
        <div className="bg-surface-container-highest border border-surface-container-high relative p-6 h-full flex flex-col">
          <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-primary-container/50 to-transparent"></div>
          <div className="font-label-caps text-label-caps text-tertiary-fixed-dim mb-6 bg-background/50 inline-block px-2 py-1 border border-outline-variant/30 w-fit">SEQ_03</div>
          <h3 className="font-body-strong text-body-strong text-on-surface mb-2">Clear risk report with recommended actions.</h3>
        </div>
      </div>
    </section>
  );
}