import React from 'react';
import TopNavBar from '../components/TopNavBar';
import HeroSection from '../components/HeroSection';
import ExampleDetection from '../components/ExampleDetection';
import ProtocolSequence from '../components/ProtocolSequence';
import HybridReasoning from '../components/HybridReasoning';
import ComparisonTable from '../components/ComparisonTable';
import Footer from '../components/Footer';

export default function LandingPage() {
  return (
    <div className="bg-[#050d1a] text-on-surface font-body-main antialiased relative min-h-screen flex flex-col selection:bg-secondary-fixed-dim selection:text-background">
      {/* Global Background Grid */}
      <div className="fixed inset-0 dot-grid pointer-events-none z-0"></div>

      <TopNavBar />

      <main className="flex-grow relative z-10 pt-[64px]">
        <HeroSection />
        <ExampleDetection />
        <ProtocolSequence />
        <HybridReasoning />
        <ComparisonTable />
      </main>

      <Footer />
    </div>
  );
}