import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ActionTracker from "./pages/ActionTracker";
import Alerts from "./pages/Alerts";
import Analytics from "./pages/Analytics";
import Dashboard from "./pages/Dashboard";
import ImpactAnalysis from "./pages/ImpactAnalysis";
import Inventory from "./pages/Inventory";
import Mitigation from "./pages/Mitigation";
import Reports from "./pages/Reports";
import ShipmentTracking from "./pages/ShipmentTracking";
import Suppliers from "./pages/Suppliers";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/suppliers" element={<Suppliers />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/shipments" element={<ShipmentTracking />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/impact" element={<ImpactAnalysis />} />
        <Route path="/mitigation" element={<Mitigation />} />
        <Route path="/actions" element={<ActionTracker />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/reports" element={<Reports />} />
      </Routes>
    </Layout>
  );
}
