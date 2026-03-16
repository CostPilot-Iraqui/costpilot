import { NavLink, useParams } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  FolderKanban,
  Calculator,
  Library,
  BarChart3,
  Target,
  AlertTriangle,
  GitCompare,
  Scale,
  TrendingUp,
  Workflow,
  CalendarDays,
  Users,
  FileText,
  Settings,
  LogOut,
  Lock,
  Building2,
  Sparkles,
  FileSpreadsheet,
  Brain,
  BookOpen,
  Code,
  FileDown,
  ScanLine,
  Layers,
  TrendingDown,
  Briefcase,
  Ruler,
  Award,
  Globe,
  Lightbulb,
  Shield,
  Leaf,
  FileBox,
  Zap,
} from 'lucide-react';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';

const mainNavItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Tableau de bord' },
  { to: '/projects', icon: FolderKanban, label: 'Projets' },
  { to: '/projects/generate-program', icon: FileText, label: 'Programme', highlight: true },
  { to: '/projects/generate-budget', icon: Sparkles, label: 'Budget auto', highlight: true },
  { to: '/instant-estimation', icon: Zap, label: 'Estimation IA', highlight: true, highlightLabel: 'IA' },
  { to: '/ai-optimization', icon: Lightbulb, label: 'Optimisation IA', highlight: true },
  { to: '/feasibility', icon: TrendingUp, label: 'Faisabilité', highlight: true },
  { to: '/benchmark', icon: BarChart3, label: 'Benchmark', highlight: true },
  { to: '/pricing-library', icon: Library, label: 'Bibliothèque prix' },
  { to: '/reference-ratios', icon: Target, label: 'Ratios référence' },
  { to: '/documentation', icon: Code, label: 'Documentation API' },
  { to: '/admin', icon: Shield, label: 'Administration', adminOnly: true },
];

const getProjectNavItems = (projectId) => [
  { to: `/projects/${projectId}`, icon: Building2, label: 'Vue d\'ensemble', end: true },
  { section: 'Modules IA Avancés' },
  { to: `/projects/${projectId}/bim-import`, icon: FileBox, label: 'Import BIM/IFC', highlight: true, highlightColor: 'emerald' },
  { to: `/projects/${projectId}/ai-plan-reading`, icon: ScanLine, label: 'Lecture IA Plans', highlight: true, highlightColor: 'violet' },
  { to: `/projects/${projectId}/instant-estimation`, icon: Zap, label: 'Estimation IA', highlight: true, highlightColor: 'amber' },
  { to: `/projects/${projectId}/cctp-generator`, icon: FileText, label: 'Générateur CCTP', highlight: true, highlightColor: 'blue' },
  { to: `/projects/${projectId}/carbon-analysis`, icon: Leaf, label: 'Analyse Carbone', highlight: true, highlightColor: 'green' },
  { section: 'Économie Senior' },
  { to: `/projects/${projectId}/senior-economist`, icon: Briefcase, label: 'Méthodologie', highlight: true, highlightColor: 'indigo' },
  { to: `/projects/${projectId}/cost-prediction`, icon: Brain, label: 'Prédiction IA', highlight: true, highlightColor: 'purple' },
  { to: `/projects/${projectId}/design-optimization`, icon: Lightbulb, label: 'Optimisation design', highlight: true, highlightColor: 'amber' },
  { to: `/projects/${projectId}/multi-scenario`, icon: Layers, label: 'Multi-scénarios', highlight: true, highlightColor: 'pink' },
  { section: 'Métier avancé' },
  { to: `/projects/${projectId}/plan-reading`, icon: ScanLine, label: 'Lecture plans', highlight: true },
  { to: `/projects/${projectId}/quantity-takeoff`, icon: Ruler, label: 'Métré auto', highlight: true },
  { to: `/projects/${projectId}/dpgf`, icon: FileSpreadsheet, label: 'DPGF auto', highlight: true },
  { to: `/projects/${projectId}/cost-optimization`, icon: TrendingDown, label: 'Optimisation IA', highlight: true },
  { section: 'Intelligence Marché' },
  { to: `/projects/${projectId}/benchmark`, icon: Award, label: 'Benchmark projets', highlight: true, highlightColor: 'emerald' },
  { to: `/projects/${projectId}/market-intelligence`, icon: Globe, label: 'Intelligence marché', highlight: true, highlightColor: 'sky' },
  { section: 'Budget' },
  { to: `/projects/${projectId}/macro-envelope`, icon: Target, label: 'Enveloppe macro' },
  { to: `/projects/${projectId}/micro-breakdown`, icon: Calculator, label: 'Détail micro' },
  { to: `/projects/${projectId}/macro-vs-micro`, icon: GitCompare, label: 'Macro vs Micro' },
  { section: 'Analyse' },
  { to: `/projects/${projectId}/ai-analysis`, icon: Brain, label: 'Diagnostic IA' },
  { to: `/projects/${projectId}/alerts`, icon: AlertTriangle, label: 'Alertes' },
  { to: `/projects/${projectId}/scenarios`, icon: Scale, label: 'Scénarios' },
  { to: `/projects/${projectId}/arbitrations`, icon: Lock, label: 'Arbitrages' },
  { to: `/projects/${projectId}/feasibility`, icon: TrendingUp, label: 'Faisabilité' },
  { section: 'Gestion' },
  { to: `/projects/${projectId}/planning`, icon: CalendarDays, label: 'Planning' },
  { to: `/projects/${projectId}/team`, icon: Users, label: 'Équipe' },
  { to: `/projects/${projectId}/decision-log`, icon: BookOpen, label: 'Journal décisions' },
  { section: 'Export' },
  { to: `/projects/${projectId}/exports`, icon: FileDown, label: 'Exports' },
  { to: `/projects/${projectId}/reports`, icon: FileText, label: 'Rapports' },
];

export function Sidebar() {
  const { projectId } = useParams();
  const { user, logout } = useAuth();

  const projectNavItems = projectId ? getProjectNavItems(projectId) : [];

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-slate-200 bg-slate-50">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-slate-200 px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900">
              <Calculator className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-900">CostPilot</span>
          </div>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-1">
            {mainNavItems
              .filter(item => !item.adminOnly || user?.role === 'administrator')
              .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'sidebar-nav-item flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'active bg-slate-100 text-slate-900'
                      : item.highlight
                        ? 'text-blue-600 hover:text-blue-700 hover:bg-blue-50'
                        : item.adminOnly
                          ? 'text-amber-600 hover:text-amber-700 hover:bg-amber-50'
                          : 'text-slate-600 hover:text-slate-900'
                  )
                }
                data-testid={`nav-${item.label.toLowerCase().replace(/['\s]/g, '-')}`}
              >
                <item.icon className={cn("h-4 w-4", item.highlight && "text-blue-500", item.adminOnly && "text-amber-500")} />
                {item.label}
                {item.highlight && (
                  <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide text-blue-500 bg-blue-100 px-1.5 py-0.5 rounded">
                    Nouveau
                  </span>
                )}
                {item.adminOnly && (
                  <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded">
                    Admin
                  </span>
                )}
              </NavLink>
            ))}
          </nav>

          {projectId && (
            <>
              <Separator className="my-4" />
              <div className="mb-2 px-3">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Projet actif
                </span>
              </div>
              <nav className="space-y-1">
                {projectNavItems.map((item, index) => {
                  if (item.section) {
                    return (
                      <div key={`section-${item.section}`} className="pt-3 pb-1 px-3">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                          {item.section}
                        </span>
                      </div>
                    );
                  }
                  
                  const highlightColors = {
                    purple: { text: 'text-purple-600 hover:text-purple-700 hover:bg-purple-50', icon: 'text-purple-500', badge: 'text-purple-500 bg-purple-100' },
                    indigo: { text: 'text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50', icon: 'text-indigo-500', badge: 'text-indigo-500 bg-indigo-100' },
                    amber: { text: 'text-amber-600 hover:text-amber-700 hover:bg-amber-50', icon: 'text-amber-500', badge: 'text-amber-500 bg-amber-100' },
                    pink: { text: 'text-pink-600 hover:text-pink-700 hover:bg-pink-50', icon: 'text-pink-500', badge: 'text-pink-500 bg-pink-100' },
                    emerald: { text: 'text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50', icon: 'text-emerald-500', badge: 'text-emerald-500 bg-emerald-100' },
                    sky: { text: 'text-sky-600 hover:text-sky-700 hover:bg-sky-50', icon: 'text-sky-500', badge: 'text-sky-500 bg-sky-100' },
                    violet: { text: 'text-violet-600 hover:text-violet-700 hover:bg-violet-50', icon: 'text-violet-500', badge: 'text-violet-500 bg-violet-100' },
                    blue: { text: 'text-blue-600 hover:text-blue-700 hover:bg-blue-50', icon: 'text-blue-500', badge: 'text-blue-500 bg-blue-100' },
                    green: { text: 'text-green-600 hover:text-green-700 hover:bg-green-50', icon: 'text-green-500', badge: 'text-green-500 bg-green-100' },
                    default: { text: 'text-purple-600 hover:text-purple-700 hover:bg-purple-50', icon: 'text-purple-500', badge: 'text-purple-500 bg-purple-100' },
                  };
                  const colors = highlightColors[item.highlightColor] || highlightColors.default;
                  
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        cn(
                          'sidebar-nav-item flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
                          isActive
                            ? 'active bg-slate-100 text-slate-900'
                            : item.highlight
                              ? colors.text
                              : 'text-slate-600 hover:text-slate-900'
                        )
                      }
                      data-testid={`nav-project-${item.label.toLowerCase().replace(/['\s]/g, '-')}`}
                    >
                      <item.icon className={cn("h-4 w-4", item.highlight && colors.icon)} />
                      {item.label}
                      {item.highlight && (
                        <span className={cn("ml-auto text-[9px] font-semibold uppercase tracking-wide px-1 py-0.5 rounded", colors.badge)}>
                          PRO
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </nav>
            </>
          )}
        </ScrollArea>

        {/* User section */}
        <div className="border-t border-slate-200 p-4">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-medium text-slate-700">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 truncate">
              <p className="truncate text-sm font-medium text-slate-900">{user?.full_name}</p>
              <p className="truncate text-xs text-slate-500">{user?.email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 justify-start text-slate-600"
              asChild
            >
              <NavLink to="/settings" data-testid="nav-settings">
                <Settings className="mr-2 h-4 w-4" />
                Paramètres
              </NavLink>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-600"
              onClick={logout}
              data-testid="logout-btn"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </aside>
  );
}
