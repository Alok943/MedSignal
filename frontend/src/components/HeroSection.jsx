import React from 'react';

export default function HeroSection() {
  return (
    <section className="px-margin py-16 max-w-container-max mx-auto border-b border-surface-container-high/50">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter items-center">
        {/* Hero Content */}
        <div className="col-span-1 md:col-span-6 flex flex-col gap-6 pr-0 md:pr-12">
          <div className="flex items-center gap-2 text-[#00d4ff] font-label-caps text-label-caps">
            <span className="w-2 h-2 bg-[#00d4ff] rounded-full animate-pulse shadow-[0_0_8px_#3cd7ff]"></span>
            SYSTEM ONLINE // AMD INSTINCT READY
          </div>
          <h1 className="font-display-lg text-display-lg text-on-surface uppercase leading-none">
            Detects Critical Risks Before They're Missed
          </h1>
          <div>
            <p className="font-body-strong text-body-strong text-tertiary-fixed-dim max-w-lg border-l-2 border-[#ED1C24] pl-4 mb-4">
    Missed life-threatening conditions like heart attacks or major
    blood vessel tears can be fatal within hours.<br />
    MedSignal detects critical patterns in real-time &mdash; before it&apos;s too late.
            </p>
            <p className="font-body-main text-sm text-tertiary-fixed-dim opacity-80 pl-4">
              Built for emergency care, triage systems, and real-time decision support.
            </p>
          </div>
          <div className="flex flex-wrap gap-4 pt-6">
            
            {/* FIXED BUTTON 1: Text glow only on hover/active, no box shadow */}
            <button className="bg-[#ED1C24] text-white font-label-caps text-[13px] px-8 py-4 uppercase transition-all duration-300 flex items-center gap-2 tracking-wider hover:[text-shadow:0_0_10px_rgba(255,255,255,0.8)] active:[text-shadow:0_0_15px_rgba(255,255,255,1)]">
              Run Emergency Case
              <span className="material-symbols-outlined text-[18px]">arrow_right_alt</span>
            </button>
            
            {/* FIXED BUTTON 2: Text glow only on hover/active, no box shadow */}
            <button className="bg-[#0f1e35] border border-[#00d4ff]/50 text-[#00d4ff] font-label-caps text-[13px] px-8 py-4 uppercase transition-all duration-300 flex items-center gap-2 tracking-wider hover:bg-[#00d4ff]/10 hover:[text-shadow:0_0_10px_rgba(0,212,255,0.8)] active:[text-shadow:0_0_15px_rgba(0,212,255,1)]">
              See Critical Detection in Action
              <span className="material-symbols-outlined text-[18px]">arrow_right_alt</span>
            </button>
            
          </div>
        </div>

        {/* Hero Visual Diagram */}
        <div className="col-span-1 md:col-span-6 flex flex-col items-center mt-12 md:mt-0">
          <div className="relative w-full h-[400px] flex items-center justify-center border border-surface-container-high/30 bg-surface-container-lowest/50 backdrop-blur-sm mb-6 overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
              <div className="w-[300px] h-[300px] rounded-full border border-secondary-fixed-dim/30 animate-[spin_60s_linear_infinite]"></div>
              <div className="w-[450px] h-[450px] rounded-full border border-secondary-fixed-dim/10 absolute animate-[spin_120s_linear_infinite_reverse]"></div>
            </div>

            {/* Diagram Nodes */}
            <div className="relative w-full max-w-[400px] h-full flex flex-col items-center justify-between py-12 z-10">
              <div className="flex flex-col items-center gap-2 z-10">
                <div className="w-12 h-12 rounded-full border-2 border-secondary-fixed-dim bg-surface-container flex items-center justify-center text-secondary-fixed-dim shadow-[0_0_15px_rgba(60,215,255,0.3)]">
                  <span className="material-symbols-outlined text-[20px]">input</span>
                </div>
                <span className="font-label-caps text-label-caps text-tertiary-fixed-dim uppercase bg-background px-2">Intake</span>
              </div>

              {/* FIXED SYMMETRY: Added w-24 to left and right nodes to keep the center perfectly aligned */}
              <div className="flex w-full justify-between items-center relative z-10 px-4">
                
                {/* Left Node (Fixed Width) */}
                <div className="w-24 flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full border border-outline-variant bg-surface-container flex items-center justify-center text-tertiary-fixed-dim">
                    <span className="material-symbols-outlined text-[20px]">rule</span>
                  </div>
                  <span className="font-label-caps text-label-caps text-tertiary-fixed-dim uppercase bg-background px-2">DDx</span>
                </div>
                
                {/* Center Target (Now perfectly symmetrical) */}
                <div className="w-20 h-20 rounded-none border border-secondary-fixed-dim/50 bg-surface-container-highest flex items-center justify-center text-secondary-fixed-dim relative shrink-0">
                  <div className="absolute inset-0 border border-secondary-fixed-dim opacity-50 scale-110"></div>
                  <span className="material-symbols-outlined text-[40px] opacity-80" style={{ fontVariationSettings: "'wght' 200" }}>person</span>
                </div>
                
                {/* Right Node (Fixed Width) */}
                <div className="w-24 flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full border-2 border-[#ED1C24] bg-surface-container flex items-center justify-center text-[#ED1C24] shadow-[0_0_15px_rgba(237,28,36,0.3)]">
                    <span className="material-symbols-outlined text-[20px]">warning</span>
                  </div>
                  <span className="font-label-caps text-label-caps text-[#ED1C24] uppercase bg-background px-2 text-center">Red Flag</span>
                </div>
              </div>

              <div className="flex w-full justify-around items-center relative z-10 px-8">
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full border border-outline-variant bg-surface-container flex items-center justify-center text-tertiary-fixed-dim">
                    <span className="material-symbols-outlined text-[20px]">fact_check</span>
                  </div>
                  <span className="font-label-caps text-label-caps text-tertiary-fixed-dim uppercase bg-background px-2">Consistency</span>
                </div>
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full border-2 border-secondary-fixed-dim bg-surface-container flex items-center justify-center text-secondary-fixed-dim shadow-[0_0_15px_rgba(60,215,255,0.3)]">
                    <span className="material-symbols-outlined text-[20px]">summarize</span>
                  </div>
                  <span className="font-label-caps text-label-caps text-secondary-fixed-dim uppercase bg-background px-2">Summary</span>
                </div>
              </div>

              {/* Connecting SVG Lines */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" style={{ stroke: "#3cd7ff", strokeWidth: "1px", opacity: 0.3, fill: "none" }}>
                <line strokeDasharray="4 4" x1="50%" x2="50%" y1="15%" y2="50%"></line>
                <line strokeDasharray="4 4" x1="20%" x2="40%" y1="50%" y2="50%"></line>
                <line x1="60%" x2="80%" y1="50%" y2="50%"></line>
                <line strokeDasharray="4 4" x1="50%" x2="30%" y1="50%" y2="85%"></line>
                <line strokeDasharray="4 4" x1="50%" x2="70%" y1="50%" y2="85%"></line>
              </svg>

              {/* Scanner Line Overlay */}
              <div className="absolute inset-0 pointer-events-none overflow-hidden z-20">
                <div className="w-full h-[2px] bg-secondary-fixed-dim/50 shadow-[0_0_8px_#3cd7ff] absolute top-0 left-0 animate-[translateY_3s_linear_infinite]" style={{ animation: "scan 4s linear infinite" }}></div>
              </div>
            </div>
          </div>
          <p className="text-sm font-data-mono text-tertiary-fixed-dim text-center max-w-md px-4">
            5 specialized agents analyze patient data in parallel — identifying dangerous symptoms,
            checking drug interactions, validating consistency, and ranking conditions in real time.
          </p>
        </div>
      </div>
      <div className="text-center mt-12 text-tertiary-fixed-dim font-label-caps text-[10px] tracking-widest uppercase">
        Designed for real-time clinical decision support
      </div>
    </section>
  );
}