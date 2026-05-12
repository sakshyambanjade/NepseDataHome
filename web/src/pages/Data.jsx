import React from 'react';
import { Database, Github, Code } from 'lucide-react';

export function DataPage() {
  return (
    <div className="max-w-6xl mx-auto py-12 px-4 animate-in fade-in duration-700">
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
