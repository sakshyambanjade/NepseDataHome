import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnalyticsDashboard } from "./Analytics";
import { Activity, Database, Info, LayoutDashboard, Menu, X, Code } from "lucide-react";

function TopNav() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  
  const links = [
    { path: "/", label: "Market Intelligence", icon: LayoutDashboard },
    { path: "/data", label: "Open Data", icon: Database },
    { path: "/about", label: "About", icon: Info },
  ];

  return (
    <nav className="glass-morphism sticky top-0 z-50 border-b border-white/5 px-4 lg:px-8 py-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-500/20">
            <Activity className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">NepSense</h1>
            <p className="text-[10px] text-gray-400 font-medium uppercase tracking-widest">Open Analytics</p>
          </div>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center space-x-1">
          {links.map((link) => {
            const Icon = link.icon;
            const active = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  active 
                    ? "bg-blue-600/10 text-blue-400 shadow-[inset_0_0_12px_rgba(59,130,246,0.1)]" 
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {link.label}
              </Link>
            );
          })}
          <div className="h-6 w-px bg-white/10 mx-4"></div>
          <a 
            href="https://github.com/sakshyambanjade/NepSense" 
            target="_blank" 
            rel="noreferrer"
            className="flex items-center text-gray-400 hover:text-white transition-colors"
          >
            <Code className="w-5 h-5 mr-2" />
            <span className="text-xs font-semibold">Open Source</span>
          </a>
        </div>

        {/* Mobile Toggle */}
        <button className="md:hidden text-white" onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 glass-morphism border-b border-white/10 p-4 space-y-2 animate-in slide-in-from-top-4 duration-300">
          {links.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setIsOpen(false)}
              className="flex items-center p-3 rounded-xl text-gray-300 hover:bg-white/5 transition-colors"
            >
              <link.icon className="w-5 h-5 mr-3 text-blue-400" />
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}

function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="glass-morphism rounded-3xl p-8 lg:p-12 border border-white/5">
        <h2 className="text-3xl font-bold text-white mb-6">About NepSense</h2>
        <div className="space-y-6 text-gray-400 leading-relaxed">
          <p>
            NepSense is an open-source data intelligence platform designed for the Nepal Stock Exchange (NEPSE).
            Our goal is to provide institutional-grade analytical tools to retail investors, for free.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6">
            <div className="p-6 bg-white/5 rounded-2xl border border-white/5">
              <h3 className="text-white font-bold mb-2">Transparency</h3>
              <p className="text-sm text-gray-500">Every calculation, indicator, and ML model is open for inspection on GitHub.</p>
            </div>
            <div className="p-6 bg-white/5 rounded-2xl border border-white/5">
              <h3 className="text-white font-bold mb-2">Accessibility</h3>
              <p className="text-sm text-gray-500">No login, no pricing, no paywalls. Just pure financial data intelligence.</p>
            </div>
          </div>
          <p className="pt-6">
            Built with ❤️ for the Nepalese investor community.
          </p>
        </div>
      </div>
    </div>
  );
}

function DataPage() {
  return (
    <div className="max-w-6xl mx-auto py-12 px-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        <div className="space-y-6">
          <h2 className="text-4xl font-black text-white leading-tight">Access the <span className="text-blue-500">Raw Data</span></h2>
          <p className="text-gray-400 text-lg">
            We believe in data sovereignty. Download our processed datasets in industry-standard formats for your own research and backtesting.
          </p>
          <div className="flex space-x-4">
            <a href="/data/public_data_book.csv" className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-all transform hover:scale-105 active:scale-95 shadow-xl shadow-blue-500/20 flex items-center">
              <Database className="w-5 h-5 mr-2" />
              Download CSV
            </a>
            <a href="https://github.com/sakshyambanjade/NepSense" className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-bold border border-white/10 transition-all flex items-center">
              <Code className="w-5 h-5 mr-2" />
              Source Code
            </a>
          </div>
        </div>
        <div className="glass-morphism rounded-3xl p-8 border border-white/5">
          <h3 className="text-xl font-bold text-white mb-6">Dataset Specs</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">Total Rows</span>
              <span className="text-white font-mono">265k+</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">Symbols Covered</span>
              <span className="text-white font-mono">360+</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">History Start</span>
              <span className="text-white font-mono">2000-01-01</span>
            </div>
            <div className="flex justify-between items-center py-3">
              <span className="text-gray-400">Update Frequency</span>
              <span className="text-blue-400 font-bold uppercase text-[10px]">Daily (End of Day)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen text-gray-100 flex flex-col">
      <TopNav />
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><AnalyticsDashboard /></div>} />
          <Route path="/data" element={<DataPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="border-t border-white/5 py-12 px-4 lg:px-8 bg-gray-950/50 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center">
          <div className="text-gray-500 text-sm mb-4 md:mb-0">
            &copy; 2026 NepSense Platform. Open source under MIT License.
          </div>
          <div className="flex space-x-6 text-gray-400">
            <a href="https://github.com/sakshyambanjade/NepSense" className="hover:text-white transition-colors flex items-center">
              <Code className="w-4 h-4 mr-2" />
              GitHub
            </a>
            <span className="text-white/10">|</span>
            <span className="text-gray-600 italic">Financial data is for informational purposes only.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
