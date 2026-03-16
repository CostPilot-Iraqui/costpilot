import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LOT_STRUCTURE } from '../../lib/lotStructure';
import { microItemsAPI, macroCategoriesAPI } from '../../lib/api';
import { formatCurrency, formatNumber, cn } from '../../lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { 
  ChevronRight, 
  ChevronDown, 
  Plus, 
  Save, 
  Trash2, 
  Search,
  Filter,
  SortAsc,
  SortDesc,
  FolderTree,
  Calculator,
  Library
} from 'lucide-react';
import { toast } from 'sonner';

// Composant ligne éditable
const EditableCell = ({ value, onChange, onBlur, type = 'text', className, disabled }) => {
  const [localValue, setLocalValue] = useState(value);
  
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  return (
    <Input
      type={type}
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      onBlur={() => {
        if (localValue !== value) {
          onBlur(localValue);
        }
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.target.blur();
        }
        if (e.key === 'Tab') {
          if (localValue !== value) {
            onBlur(localValue);
          }
        }
      }}
      disabled={disabled}
      className={cn(
        "h-8 border-0 bg-transparent focus:bg-white focus:border focus:border-blue-500 rounded-none",
        type === 'number' && "text-right tabular-nums",
        className
      )}
    />
  );
};

// Composant ligne de sous-lot
const SublotRow = ({ 
  sublot, 
  item, 
  onUpdate, 
  onDelete, 
  canEdit, 
  projectSurface,
  isEven
}) => {
  const amount = item ? item.quantity * item.unit_price : 0;
  const ratio = projectSurface > 0 ? amount / projectSurface : 0;

  if (!item) {
    // Ligne vide pour ce sous-lot (pas encore de poste)
    return (
      <tr className={cn(
        "border-b border-slate-100 hover:bg-blue-50/30 transition-colors",
        isEven ? "bg-slate-50/30" : "bg-white"
      )}>
        <td className="px-2 py-1 pl-12 text-xs font-mono text-slate-400">{sublot.code}</td>
        <td className="px-2 py-1 text-sm text-slate-500 italic">{sublot.name}</td>
        <td className="px-2 py-1 text-center text-xs text-slate-400">{sublot.unit}</td>
        <td className="px-2 py-1 text-right text-xs text-slate-400">-</td>
        <td className="px-2 py-1 text-right text-xs text-slate-400">{formatCurrency(sublot.avgPrice)}</td>
        <td className="px-2 py-1 text-right text-xs text-slate-400">-</td>
        <td className="px-2 py-1 text-right text-xs text-slate-400">-</td>
        <td className="px-2 py-1 w-10"></td>
      </tr>
    );
  }

  return (
    <tr className={cn(
      "border-b border-slate-100 hover:bg-blue-50/50 transition-colors group",
      isEven ? "bg-slate-50/30" : "bg-white"
    )} data-testid={`row-${item.id}`}>
      <td className="px-2 py-1 pl-12">
        <span className="text-xs font-mono text-slate-500">{item.item_code}</span>
      </td>
      <td className="px-2 py-1">
        {canEdit ? (
          <EditableCell
            value={item.description}
            onBlur={(val) => onUpdate(item.id, 'description', val)}
            className="w-full text-sm"
          />
        ) : (
          <span className="text-sm text-slate-900">{item.description}</span>
        )}
      </td>
      <td className="px-2 py-1 text-center text-xs text-slate-600">{item.unit}</td>
      <td className="px-2 py-1 w-24">
        {canEdit ? (
          <EditableCell
            value={item.quantity}
            type="number"
            onBlur={(val) => onUpdate(item.id, 'quantity', parseFloat(val) || 0)}
            className="w-full text-xs"
          />
        ) : (
          <span className="text-xs tabular-nums text-right block">{formatNumber(item.quantity)}</span>
        )}
      </td>
      <td className="px-2 py-1 w-28">
        {canEdit ? (
          <EditableCell
            value={item.unit_price}
            type="number"
            onBlur={(val) => onUpdate(item.id, 'unit_price', parseFloat(val) || 0)}
            className="w-full text-xs"
          />
        ) : (
          <span className="text-xs tabular-nums text-right block">{formatCurrency(item.unit_price)}</span>
        )}
      </td>
      <td className="px-2 py-1 text-right">
        <span className="text-xs font-medium tabular-nums text-slate-900">{formatCurrency(amount)}</span>
      </td>
      <td className="px-2 py-1 text-right">
        <span className="text-xs tabular-nums text-slate-500">{formatCurrency(ratio)}/m²</span>
      </td>
      <td className="px-2 py-1 w-10">
        {canEdit && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700"
            onClick={() => onDelete(item.id)}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        )}
      </td>
    </tr>
  );
};

// Composant ligne de lot (groupe)
const LotRow = ({ 
  lot, 
  items, 
  isExpanded, 
  onToggle, 
  onUpdate, 
  onDelete, 
  onAddItem,
  canEdit,
  projectSurface,
  macroCategoryId,
  projectId
}) => {
  const lotItems = items.filter(item => item.lot_code === lot.code);
  const lotTotal = lotItems.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  const lotRatio = projectSurface > 0 ? lotTotal / projectSurface : 0;

  return (
    <>
      {/* Ligne du lot (header) */}
      <tr 
        className="bg-slate-100 border-b border-slate-200 cursor-pointer hover:bg-slate-200/70 transition-colors"
        onClick={onToggle}
        data-testid={`lot-row-${lot.code}`}
      >
        <td className="px-2 py-2 pl-6">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-slate-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-slate-500" />
            )}
            <span className="text-xs font-mono font-semibold text-slate-700">{lot.code}</span>
          </div>
        </td>
        <td className="px-2 py-2">
          <span className="text-sm font-medium text-slate-800">{lot.name}</span>
          <span className="ml-2 text-xs text-slate-500">({lotItems.length} postes)</span>
        </td>
        <td className="px-2 py-2"></td>
        <td className="px-2 py-2"></td>
        <td className="px-2 py-2"></td>
        <td className="px-2 py-2 text-right">
          <span className="text-sm font-semibold tabular-nums text-slate-900">{formatCurrency(lotTotal)}</span>
        </td>
        <td className="px-2 py-2 text-right">
          <span className="text-xs tabular-nums text-slate-600">{formatCurrency(lotRatio)}/m²</span>
        </td>
        <td className="px-2 py-2 w-10">
          {canEdit && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation();
                onAddItem(lot);
              }}
              title="Ajouter un poste"
            >
              <Plus className="h-3 w-3" />
            </Button>
          )}
        </td>
      </tr>

      {/* Sous-lots et postes */}
      {isExpanded && lot.sublots.map((sublot, idx) => {
        const sublotItem = lotItems.find(item => item.sub_lot_code === sublot.code);
        return (
          <SublotRow
            key={sublot.code}
            sublot={sublot}
            item={sublotItem}
            onUpdate={onUpdate}
            onDelete={onDelete}
            canEdit={canEdit}
            projectSurface={projectSurface}
            isEven={idx % 2 === 0}
          />
        );
      })}

      {/* Postes personnalisés (pas dans la structure standard) */}
      {isExpanded && lotItems
        .filter(item => !lot.sublots.find(s => s.code === item.sub_lot_code))
        .map((item, idx) => (
          <SublotRow
            key={item.id}
            sublot={{ code: item.sub_lot_code || item.item_code, name: item.description, unit: item.unit, avgPrice: item.unit_price }}
            item={item}
            onUpdate={onUpdate}
            onDelete={onDelete}
            canEdit={canEdit}
            projectSurface={projectSurface}
            isEven={(lot.sublots.length + idx) % 2 === 0}
          />
        ))}
    </>
  );
};

// Composant principal du tableur
export default function MicroSpreadsheet({ 
  projectId, 
  project, 
  categories, 
  items, 
  onRefresh,
  canEdit 
}) {
  const [expandedCategories, setExpandedCategories] = useState({});
  const [expandedLots, setExpandedLots] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [addingToLot, setAddingToLot] = useState(null);
  const [newItemForm, setNewItemForm] = useState({
    sub_lot_code: '',
    description: '',
    unit: '',
    quantity: '',
    unit_price: ''
  });

  const projectSurface = project?.target_surface_m2 || 1;

  // Toggle expansion
  const toggleCategory = (catCode) => {
    setExpandedCategories(prev => ({
      ...prev,
      [catCode]: !prev[catCode]
    }));
  };

  const toggleLot = (lotCode) => {
    setExpandedLots(prev => ({
      ...prev,
      [lotCode]: !prev[lotCode]
    }));
  };

  // Expand all / Collapse all
  const expandAll = () => {
    const allCats = {};
    const allLots = {};
    Object.keys(LOT_STRUCTURE).forEach(catCode => {
      allCats[catCode] = true;
      LOT_STRUCTURE[catCode].lots.forEach(lot => {
        allLots[lot.code] = true;
      });
    });
    setExpandedCategories(allCats);
    setExpandedLots(allLots);
  };

  const collapseAll = () => {
    setExpandedCategories({});
    setExpandedLots({});
  };

  // Update item
  const handleUpdateItem = async (itemId, field, value) => {
    try {
      await microItemsAPI.update(projectId, itemId, { [field]: value });
      toast.success('Mis à jour');
      onRefresh();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  // Delete item
  const handleDeleteItem = async (itemId) => {
    try {
      await microItemsAPI.delete(projectId, itemId);
      toast.success('Poste supprimé');
      onRefresh();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  // Add item to lot
  const handleAddItem = async () => {
    if (!addingToLot || !newItemForm.description) {
      toast.error('Veuillez remplir les champs requis');
      return;
    }

    try {
      // Find the macro category for this lot
      const catCode = addingToLot.code.split('.')[0];
      const category = categories.find(c => c.code === catCode);
      
      if (!category) {
        toast.error('Catégorie non trouvée');
        return;
      }

      await microItemsAPI.create(projectId, {
        project_id: projectId,
        macro_category_id: category.id,
        lot_code: addingToLot.code,
        lot_name: addingToLot.name,
        sub_lot_code: newItemForm.sub_lot_code || `${addingToLot.code}.${String(Date.now()).slice(-3)}`,
        sub_lot_name: newItemForm.description,
        item_code: newItemForm.sub_lot_code || `${addingToLot.code}.${String(Date.now()).slice(-3)}`,
        description: newItemForm.description,
        unit: newItemForm.unit || 'u',
        quantity: parseFloat(newItemForm.quantity) || 0,
        unit_price: parseFloat(newItemForm.unit_price) || 0,
      });

      toast.success('Poste ajouté');
      setAddingToLot(null);
      setNewItemForm({ sub_lot_code: '', description: '', unit: '', quantity: '', unit_price: '' });
      onRefresh();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  // Calculate totals
  const totals = useMemo(() => {
    const total = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
    return {
      total,
      ratio: projectSurface > 0 ? total / projectSurface : 0,
      count: items.length
    };
  }, [items, projectSurface]);

  // Filter items by search
  const filteredItems = useMemo(() => {
    if (!searchTerm) return items;
    const term = searchTerm.toLowerCase();
    return items.filter(item => 
      item.description.toLowerCase().includes(term) ||
      item.lot_code.toLowerCase().includes(term) ||
      item.item_code.toLowerCase().includes(term)
    );
  }, [items, searchTerm]);

  // Get items by category
  const getItemsForCategory = (catCode) => {
    return filteredItems.filter(item => {
      const itemCatCode = item.lot_code.split('.')[0];
      return itemCatCode === catCode;
    });
  };

  // Calculate category total
  const getCategoryTotal = (catCode) => {
    const catItems = getItemsForCategory(catCode);
    return catItems.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  };

  return (
    <div className="space-y-4" data-testid="micro-spreadsheet">
      {/* Toolbar */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  placeholder="Rechercher un poste..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-64"
                  data-testid="search-input"
                />
              </div>
              <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
                <Button variant="ghost" size="sm" onClick={expandAll}>
                  <FolderTree className="h-4 w-4 mr-1" />
                  Tout déplier
                </Button>
                <Button variant="ghost" size="sm" onClick={collapseAll}>
                  Tout replier
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg">
                <Calculator className="h-4 w-4 text-slate-500" />
                <span className="text-slate-600">{totals.count} postes</span>
                <span className="font-semibold text-slate-900">{formatCurrency(totals.total)}</span>
                <span className="text-slate-500">({formatCurrency(totals.ratio)}/m²)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Spreadsheet */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="spreadsheet-table">
            <thead className="sticky top-0 z-10">
              <tr className="bg-slate-800 text-white">
                <th className="px-2 py-3 text-left text-xs font-semibold uppercase tracking-wider w-32">Code</th>
                <th className="px-2 py-3 text-left text-xs font-semibold uppercase tracking-wider">Description</th>
                <th className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider w-16">Unité</th>
                <th className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider w-24">Quantité</th>
                <th className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider w-28">Prix unit.</th>
                <th className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider w-32">Montant</th>
                <th className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider w-24">Ratio/m²</th>
                <th className="px-2 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(LOT_STRUCTURE).map(([catCode, category]) => {
                const catItems = getItemsForCategory(catCode);
                const catTotal = getCategoryTotal(catCode);
                const catRatio = projectSurface > 0 ? catTotal / projectSurface : 0;
                const macroCategory = categories.find(c => c.code === catCode);
                const isExpanded = expandedCategories[catCode];

                return (
                  <React.Fragment key={catCode}>
                    {/* Category row */}
                    <tr 
                      className="bg-slate-700 text-white cursor-pointer hover:bg-slate-600 transition-colors"
                      onClick={() => toggleCategory(catCode)}
                      data-testid={`category-row-${catCode}`}
                    >
                      <td className="px-2 py-3">
                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronDown className="h-5 w-5" />
                          ) : (
                            <ChevronRight className="h-5 w-5" />
                          )}
                          <Badge variant="outline" className="bg-white/10 text-white border-white/20 font-mono">
                            {catCode}
                          </Badge>
                        </div>
                      </td>
                      <td className="px-2 py-3">
                        <span className="font-semibold">{category.name}</span>
                        <span className="ml-2 text-xs opacity-70">({catItems.length} postes)</span>
                      </td>
                      <td className="px-2 py-3"></td>
                      <td className="px-2 py-3"></td>
                      <td className="px-2 py-3"></td>
                      <td className="px-2 py-3 text-right">
                        <div className="space-y-0.5">
                          <div className="font-semibold tabular-nums">{formatCurrency(catTotal)}</div>
                          {macroCategory && (
                            <div className={cn(
                              "text-xs",
                              catTotal > macroCategory.target_amount ? "text-red-300" : "text-green-300"
                            )}>
                              Cible: {formatCurrency(macroCategory.target_amount)}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-2 py-3 text-right">
                        <span className="tabular-nums text-sm">{formatCurrency(catRatio)}/m²</span>
                      </td>
                      <td className="px-2 py-3"></td>
                    </tr>

                    {/* Lots */}
                    {isExpanded && category.lots.map(lot => (
                      <LotRow
                        key={lot.code}
                        lot={lot}
                        items={catItems}
                        isExpanded={expandedLots[lot.code]}
                        onToggle={() => toggleLot(lot.code)}
                        onUpdate={handleUpdateItem}
                        onDelete={handleDeleteItem}
                        onAddItem={(lot) => setAddingToLot(lot)}
                        canEdit={canEdit}
                        projectSurface={projectSurface}
                        macroCategoryId={macroCategory?.id}
                        projectId={projectId}
                      />
                    ))}
                  </React.Fragment>
                );
              })}

              {/* Footer total */}
              <tr className="bg-slate-900 text-white font-semibold sticky bottom-0">
                <td colSpan={5} className="px-2 py-3 text-right">
                  TOTAL GÉNÉRAL
                </td>
                <td className="px-2 py-3 text-right tabular-nums text-lg">
                  {formatCurrency(totals.total)}
                </td>
                <td className="px-2 py-3 text-right tabular-nums">
                  {formatCurrency(totals.ratio)}/m²
                </td>
                <td className="px-2 py-3"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add item dialog */}
      {addingToLot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg mx-4">
            <CardHeader>
              <CardTitle className="text-lg">
                Ajouter un poste à {addingToLot.code} - {addingToLot.name}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-700">Code sous-lot</label>
                  <Input
                    placeholder={`${addingToLot.code}.XX`}
                    value={newItemForm.sub_lot_code}
                    onChange={(e) => setNewItemForm(prev => ({ ...prev, sub_lot_code: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Unité</label>
                  <Input
                    placeholder="m², ml, u..."
                    value={newItemForm.unit}
                    onChange={(e) => setNewItemForm(prev => ({ ...prev, unit: e.target.value }))}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Description *</label>
                <Input
                  placeholder="Description du poste..."
                  value={newItemForm.description}
                  onChange={(e) => setNewItemForm(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-700">Quantité</label>
                  <Input
                    type="number"
                    placeholder="Quantité"
                    value={newItemForm.quantity}
                    onChange={(e) => setNewItemForm(prev => ({ ...prev, quantity: e.target.value }))}
                    data-testid="input-quantity"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Prix unitaire (€)</label>
                  <Input
                    type="number"
                    placeholder="Prix €"
                    value={newItemForm.unit_price}
                    onChange={(e) => setNewItemForm(prev => ({ ...prev, unit_price: e.target.value }))}
                    data-testid="input-unit-price"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => setAddingToLot(null)}>
                  Annuler
                </Button>
                <Button onClick={handleAddItem} data-testid="confirm-add-item">
                  <Plus className="h-4 w-4 mr-2" />
                  Ajouter
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
