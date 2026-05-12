import React from 'react';

export function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4 animate-in fade-in duration-700">
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
