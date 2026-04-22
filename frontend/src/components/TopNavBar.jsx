import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const NAV_LINKS = [
  { label: 'Dashboard',   to: '/' },
  { label: 'Diagnostics', to: '/analysis' },
  { label: 'Demo Cases',  to: '/demo' },
  { label: 'Agents',      to: '/agents' },
  { label: 'Telemetry',   to: '#' },
];

export default function TopNavBar() {
  const { pathname } = useLocation();

  return (
    <nav className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-6 h-16 bg-[#050d1a]/80 backdrop-blur-md border-b border-[#7a90b0]/20">
      <Link to="/" className="flex items-center gap-2 text-xl font-black text-[#ED1C24] tracking-tighter" style={{ textDecoration:'none' }}>
        <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
          medical_services
        </span>
        MEDSIGNAL
      </Link>

      <div className="hidden md:flex items-center gap-8">
        {NAV_LINKS.map((item) => {
          const active = pathname === item.to;
          return (
            <Link
              key={item.label}
              to={item.to}
              style={{ textDecoration: 'none' }}
              className={[
                "font-['Space_Grotesk'] uppercase tracking-wider text-xs px-2 py-1 transition-colors duration-100",
                active
                  ? 'text-white border-b border-[#ED1C24]'
                  : 'text-[#7a90b0] opacity-70 hover:text-[#00d4ff] hover:bg-[#0f1e35]',
              ].join(' ')}
            >
              {item.label}
            </Link>
          );
        })}
      </div>

      <Link to="/analysis" style={{ textDecoration:'none' }}>
        <button className="bg-[#ED1C24] text-white px-4 py-2 font-['Space_Grotesk'] uppercase tracking-wider text-xs flex items-center gap-2 transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(255,255,255,0.85)]">
          Try It Now
          <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
        </button>
      </Link>
    </nav>
  );
}