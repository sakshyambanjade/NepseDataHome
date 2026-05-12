import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, LayoutDashboard, Database, Info, Menu, X, Code } from 'lucide-react';

export function TopNav() {
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
            <span className="text-xs font-semibold">Source</span>
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

export function Footer() {
  return (
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
  );
}
