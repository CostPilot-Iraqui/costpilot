import React from 'react';
import { useLocation } from 'react-router-dom';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../ui/breadcrumb';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Search, Bell } from 'lucide-react';

const routeLabels = {
  dashboard: 'Tableau de bord',
  projects: 'Projets',
  'pricing-library': 'Bibliothèque prix',
  'reference-ratios': 'Ratios référence',
  settings: 'Paramètres',
  'macro-envelope': 'Enveloppe macro',
  'micro-breakdown': 'Détail micro',
  'macro-vs-micro': 'Macro vs Micro',
  alerts: 'Alertes',
  scenarios: 'Scénarios',
  arbitrations: 'Arbitrages',
  feasibility: 'Faisabilité',
  workflow: 'Workflow',
  planning: 'Planning',
  team: 'Équipe',
  reports: 'Rapports',
  new: 'Nouveau projet',
};

export function Header() {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);

  const getBreadcrumbs = () => {
    const breadcrumbs = [];
    let currentPath = '';

    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === pathSegments.length - 1;
      const label = routeLabels[segment] || segment;

      // Skip UUID-like segments in the display but keep in path
      const isUUID = segment.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);

      if (!isUUID) {
        breadcrumbs.push({
          label,
          path: currentPath,
          isLast,
        });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="glass-header sticky top-0 z-30 flex h-16 items-center justify-between px-6">
      <Breadcrumb>
        <BreadcrumbList>
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.path}>
              {index > 0 && <BreadcrumbSeparator />}
              <BreadcrumbItem>
                {crumb.isLast ? (
                  <BreadcrumbPage className="font-medium text-slate-900">
                    {crumb.label}
                  </BreadcrumbPage>
                ) : (
                  <BreadcrumbLink href={crumb.path} className="text-slate-500 hover:text-slate-900">
                    {crumb.label}
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </React.Fragment>
          ))}
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            type="search"
            placeholder="Rechercher..."
            className="w-64 pl-9"
            data-testid="global-search"
          />
        </div>
        <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
          <Bell className="h-5 w-5 text-slate-500" />
        </Button>
      </div>
    </header>
  );
}
