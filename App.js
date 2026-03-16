import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { MainLayout } from "./components/layout/MainLayout";
import { Toaster } from "./components/ui/sonner";

// Auth pages
import LoginPage from "./pages/auth/LoginPage";

// Dashboard
import DashboardPage from "./pages/dashboard/DashboardPage";

// Projects
import ProjectsListPage from "./pages/projects/ProjectsListPage";
import NewProjectPage from "./pages/projects/NewProjectPage";
import BudgetGeneratorPage from "./pages/projects/BudgetGeneratorPage";
import ProgramGeneratorPage from "./pages/projects/ProgramGeneratorPage";
import ProjectDetailPage from "./pages/projects/ProjectDetailPage";
import MacroEnvelopePage from "./pages/projects/MacroEnvelopePage";
import MicroBreakdownPage from "./pages/projects/MicroBreakdownPage";
import MacroVsMicroPage from "./pages/projects/MacroVsMicroPage";
import AlertsPage from "./pages/projects/AlertsPage";
import ScenariosPage from "./pages/projects/ScenariosPage";
import ArbitrationsPage from "./pages/projects/ArbitrationsPage";
import ReportsPage from "./pages/projects/ReportsPage";
import ProjectAnalysisPage from "./pages/projects/ProjectAnalysisPage";
import FeasibilityPage from "./pages/projects/FeasibilityPage";
import PlanningPage from "./pages/projects/PlanningPage";
import TeamPage from "./pages/projects/TeamPage";
import ExportsPage from "./pages/projects/ExportsPage";
import AIAnalysisPage from "./pages/projects/AIAnalysisPage";
import DecisionLogPage from "./pages/projects/DecisionLogPage";
import PlanReadingPage from "./pages/projects/PlanReadingPage";
import DPGFGeneratorPage from "./pages/projects/DPGFGeneratorPage";
import CostOptimizationPage from "./pages/projects/CostOptimizationPage";
import SeniorEconomistPage from "./pages/projects/SeniorEconomistPage";
import QuantityTakeoffPage from "./pages/projects/QuantityTakeoffPage";
import ProjectBenchmarkPage from "./pages/projects/ProjectBenchmarkPage";
import MarketIntelligencePage from "./pages/projects/MarketIntelligencePage";
import CostPredictionPage from "./pages/projects/CostPredictionPage";
import DesignOptimizationPage from "./pages/projects/DesignOptimizationPage";
import MultiScenarioPage from "./pages/projects/MultiScenarioPage";
import BIMImportPage from "./pages/projects/BIMImportPage";
import InstantEstimationPage from "./pages/projects/InstantEstimationPage";
import CCTPGeneratorPage from "./pages/projects/CCTPGeneratorPage";
import CarbonAnalysisPage from "./pages/projects/CarbonAnalysisPage";
import AIPlanReadingPage from "./pages/projects/AIPlanReadingPage";

// Library
import PricingLibraryPage from "./pages/library/PricingLibraryPage";
import ReferenceRatiosPage from "./pages/library/ReferenceRatiosPage";

// Misc
import SettingsPage from "./pages/misc/SettingsPage";
import APIDocumentationPage from "./pages/misc/APIDocumentationPage";
import { WorkflowPage } from "./pages/misc/PlaceholderPages";

// Admin
import AdminPage from "./pages/AdminPage";

// Advanced Modules
import AIOptimizationPage from "./pages/AIOptimizationPage";
import FeasibilitySimulationPage from "./pages/FeasibilitySimulationPage";
import BenchmarkPage from "./pages/BenchmarkPage";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Protected routes */}
          <Route element={<MainLayout />}>
            {/* Dashboard */}
            <Route path="/dashboard" element={<DashboardPage />} />
            
            {/* Projects */}
            <Route path="/projects" element={<ProjectsListPage />} />
            <Route path="/projects/new" element={<NewProjectPage />} />
            <Route path="/projects/generate-budget" element={<BudgetGeneratorPage />} />
            <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            <Route path="/projects/:projectId/macro-envelope" element={<MacroEnvelopePage />} />
            <Route path="/projects/:projectId/micro-breakdown" element={<MicroBreakdownPage />} />
            <Route path="/projects/:projectId/macro-vs-micro" element={<MacroVsMicroPage />} />
            <Route path="/projects/:projectId/alerts" element={<AlertsPage />} />
            <Route path="/projects/:projectId/analysis" element={<ProjectAnalysisPage />} />
            <Route path="/projects/:projectId/scenarios" element={<ScenariosPage />} />
            <Route path="/projects/:projectId/arbitrations" element={<ArbitrationsPage />} />
            <Route path="/projects/:projectId/feasibility" element={<FeasibilityPage />} />
            <Route path="/projects/:projectId/workflow" element={<WorkflowPage />} />
            <Route path="/projects/:projectId/planning" element={<PlanningPage />} />
            <Route path="/projects/:projectId/team" element={<TeamPage />} />
            <Route path="/projects/:projectId/reports" element={<ReportsPage />} />
            <Route path="/projects/:projectId/exports" element={<ExportsPage />} />
            <Route path="/projects/:projectId/ai-analysis" element={<AIAnalysisPage />} />
            <Route path="/projects/:projectId/decision-log" element={<DecisionLogPage />} />
            <Route path="/projects/:projectId/plan-reading" element={<PlanReadingPage />} />
            <Route path="/projects/:projectId/dpgf" element={<DPGFGeneratorPage />} />
            <Route path="/projects/:projectId/cost-optimization" element={<CostOptimizationPage />} />
            <Route path="/projects/:projectId/senior-economist" element={<SeniorEconomistPage />} />
            <Route path="/projects/:projectId/quantity-takeoff" element={<QuantityTakeoffPage />} />
            <Route path="/projects/:projectId/benchmark" element={<ProjectBenchmarkPage />} />
            <Route path="/projects/:projectId/market-intelligence" element={<MarketIntelligencePage />} />
            <Route path="/projects/:projectId/cost-prediction" element={<CostPredictionPage />} />
            <Route path="/projects/:projectId/design-optimization" element={<DesignOptimizationPage />} />
            <Route path="/projects/:projectId/multi-scenario" element={<MultiScenarioPage />} />
            <Route path="/projects/:projectId/bim-import" element={<BIMImportPage />} />
            <Route path="/projects/:projectId/instant-estimation" element={<InstantEstimationPage />} />
            <Route path="/projects/:projectId/cctp-generator" element={<CCTPGeneratorPage />} />
            <Route path="/projects/:projectId/carbon-analysis" element={<CarbonAnalysisPage />} />
            <Route path="/projects/:projectId/ai-plan-reading" element={<AIPlanReadingPage />} />
            
            {/* Global Instant Estimation (without project) */}
            <Route path="/instant-estimation" element={<InstantEstimationPage />} />
            
            {/* Program and Budget Generators */}
            <Route path="/projects/generate-program" element={<ProgramGeneratorPage />} />
            
            {/* Library */}
            <Route path="/pricing-library" element={<PricingLibraryPage />} />
            <Route path="/reference-ratios" element={<ReferenceRatiosPage />} />
            
            {/* API Documentation */}
            <Route path="/documentation" element={<APIDocumentationPage />} />
            
            {/* Settings */}
            <Route path="/settings" element={<SettingsPage />} />
            
            {/* Admin */}
            <Route path="/admin" element={<AdminPage />} />
            
            {/* Advanced Modules */}
            <Route path="/ai-optimization" element={<AIOptimizationPage />} />
            <Route path="/feasibility" element={<FeasibilitySimulationPage />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
          </Route>
          
          {/* Redirects */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
