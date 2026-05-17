import { Navigate, Route, Routes } from "react-router-dom";
import { TopNav, Footer } from "./components/Layout";
import { AnalyticsDashboard } from "./pages/Analytics";
import { BrokerIntelligence } from "./pages/BrokerIntelligence";
import { OperatorWatch } from "./pages/OperatorWatch";
import { DataPage } from "./pages/Data";
import { AboutPage } from "./pages/About";
import { FlowsheetIntelligence } from "./pages/FlowsheetIntelligence";
import { SymbolFlowDetail } from "./pages/SymbolFlowDetail";
import { BrokerDetail } from "./pages/BrokerDetail";
import { HoldingIntelligence } from "./pages/HoldingIntelligence";
import { DailyReport } from "./pages/DailyReport";
import { BrokerNetwork } from "./pages/BrokerNetwork";
import { FlowMap } from "./pages/FlowMap";

function App() {
  return (
    <div className="min-h-screen text-gray-100 flex flex-col">
      <TopNav />
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><AnalyticsDashboard /></div>} />
          <Route path="/operator" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><OperatorWatch /></div>} />
          <Route path="/brokers" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><BrokerIntelligence /></div>} />
          <Route path="/broker/:brokerId" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><BrokerDetail /></div>} />
          <Route path="/flowsheet" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><FlowsheetIntelligence /></div>} />
          <Route path="/flowsheet/:symbol" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><SymbolFlowDetail /></div>} />
          <Route path="/holdings" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><HoldingIntelligence /></div>} />
          <Route path="/report" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><DailyReport /></div>} />
          <Route path="/network" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><BrokerNetwork /></div>} />
          <Route path="/flow" element={<div className="max-w-7xl mx-auto py-8 lg:py-12 px-4 lg:px-8"><FlowMap /></div>} />
          <Route path="/data" element={<DataPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default App;
