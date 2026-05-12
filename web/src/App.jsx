import { Navigate, Route, Routes } from "react-router-dom";
import { TopNav, Footer } from "./components/Layout";
import { AnalyticsDashboard } from "./pages/Analytics";
import { DataPage } from "./pages/Data";
import { AboutPage } from "./pages/About";

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
      <Footer />
    </div>
  );
}

export default App;
