import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-[#050d1a] border-t border-[#7a90b0]/20 w-full py-8 px-6 flex flex-col md:flex-row justify-between items-center gap-4 mt-auto z-10 relative">
      <div className="text-[#ED1C24] font-bold font-['JetBrains_Mono'] text-[10px] tracking-tight uppercase">
        © 2026 MEDSIGNAL TACTICAL AI - AMD HACKATHON PROTOCOL
      </div>
      <div className="flex flex-wrap justify-center gap-4 md:gap-6">
        <a href="https://github.com/Alok943/MedSignal" target="_blank" rel="noreferrer"
          className="font-['JetBrains_Mono'] text-[10px] tracking-tight text-[#7a90b0] hover:text-white transition-colors uppercase">
          GitHub Repository
        </a>
        {['Documentation', 'System Status', 'Privacy Log'].map((link) => (
          <a key={link} href="#"
            className="font-['JetBrains_Mono'] text-[10px] tracking-tight text-[#7a90b0] hover:text-white transition-colors uppercase">
            {link}
          </a>
        ))}
      </div>
    </footer>
  );
}