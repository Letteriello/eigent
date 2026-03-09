// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

import MemorySummary from '@/components/MemorySummary';
import SearchInput from '@/components/SearchInput';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  useMemoryStore,
  type Memory,
  type MemoryType,
} from '@/store/memoryStore';
import { Brain, Plus, Trash2, Edit, Filter, Settings, BarChart3, Database, KeyRound } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

const MEMORY_TYPES: { value: MemoryType; label: string }[] = [
  { value: 'fact', label: 'memory-fact' },
  { value: 'preference', label: 'memory-preference' },
  { value: 'context', label: 'memory-context' },
  { value: 'learned', label: 'memory-learned' },
];

export default function MemoryPage() {
  const { t } = useTranslation();
  const {
    memories,
    searchResults,
    stats,
    isLoading,
    error,
    fetchMemories,
    createMemory,
    updateMemory,
    deleteMemory,
    searchMemories,
    fetchStats,
    exportMemories,
    importMemories,
  } = useMemoryStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<MemoryType | 'all'>('all');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [memoryToDelete, setMemoryToDelete] = useState<Memory | null>(null);
  const [memoryToEdit, setMemoryToEdit] = useState<Memory | null>(null);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importData, setImportData] = useState('');

  // Form state
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState<MemoryType>('fact');
  const [editContent, setEditContent] = useState('');
  const [editType, setEditType] = useState<MemoryType>('fact');

  // Load memories on mount
  useEffect(() => {
    fetchMemories();
    fetchStats();
  }, [fetchMemories, fetchStats]);

  // Search handler
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (query.trim()) {
      searchMemories(query);
    }
  };

  // Display memories (filtered by search and type)
  const displayedMemories = useMemo(() => {
    let result = searchQuery.trim() && searchResults.length > 0 ? searchResults : memories;

    // Apply type filter
    if (typeFilter !== 'all') {
      result = result.filter((m) => m.memory_type === typeFilter);
    }

    return result;
  }, [searchQuery, searchResults, memories, typeFilter]);

  // Add memory
  const handleAddMemory = async () => {
    if (!newContent.trim()) return;

    const result = await createMemory(newContent, newType);
    if (result) {
      setAddDialogOpen(false);
      setNewContent('');
      setNewType('fact');
      fetchStats();
    }
  };

  // Delete memory
  const handleDeleteClick = (memory: Memory) => {
    setMemoryToDelete(memory);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (memoryToDelete) {
      await deleteMemory(memoryToDelete.id);
      setDeleteDialogOpen(false);
      setMemoryToDelete(null);
      fetchStats();
    }
  };

  // Edit memory
  const handleEditClick = (memory: Memory) => {
    setMemoryToEdit(memory);
    setEditContent(memory.content);
    setEditType(memory.memory_type);
    setEditDialogOpen(true);
  };

  const handleEditSave = async () => {
    if (!memoryToEdit || !editContent.trim()) return;

    const result = await updateMemory(
      memoryToEdit.id,
      editContent,
      editType,
      memoryToEdit.metadata
    );
    if (result) {
      setEditDialogOpen(false);
      setMemoryToEdit(null);
      setEditContent('');
      fetchStats();
    }
  };

  // Export memories
  const handleExport = async () => {
    const result = await exportMemories();
    if (result) {
      console.log('Memories exported successfully');
    }
  };

  // Import memories
  const handleImport = async () => {
    if (!importData.trim()) return;

    const count = await importMemories(importData);
    if (count > 0) {
      setImportDialogOpen(false);
      setImportData('');
      alert(`Successfully imported ${count} memories`);
    }
  };

  // File input handler for import
  const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setImportData(content);
      setImportDialogOpen(true);
    };
    reader.readAsText(file);
  };

  const getTypeLabel = (type: MemoryType) => {
    const found = MEMORY_TYPES.find((t) => t.value === type);
    return found ? t(found.label) : type;
  };

  const getTypeColor = (type: MemoryType) => {
    switch (type) {
      case 'fact':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'preference':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'context':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'learned':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="m-auto flex h-auto w-full flex-1 flex-col">
      {/* Header Section */}
      <div className="flex w-full items-center justify-between px-6 pb-4 pt-8">
        <div className="text-heading-sm font-bold text-text-heading">
          {t('agents.memory')}
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="px-6">
        <Tabs defaultValue="memories" className="w-full">
          <TabsList variant="outline" className="mb-4 w-full justify-start">
            <TabsTrigger value="memories" className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Memórias
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Estatísticas
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Configurações
            </TabsTrigger>
            <TabsTrigger value="backup" className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Backup
            </TabsTrigger>
          </TabsList>

          {/* ========== TAB: MEMORIES ========== */}
          <TabsContent value="memories">
            <div className="flex justify-end px-6 pb-4">
              <Button onClick={() => setAddDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                {t('agents.memory-add-new')}
              </Button>
            </div>

            {/* Stats Cards */}
            {stats && (
        <div className="mb-6 grid grid-cols-1 gap-4 px-6 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>{t('agents.memory-total')}</CardDescription>
              <CardTitle className="text-2xl">{stats.total_memories}</CardTitle>
            </CardHeader>
          </Card>
          {MEMORY_TYPES.map((type) => (
            <Card key={type.value}>
              <CardHeader className="pb-2">
                <CardDescription>{t(type.label)}</CardDescription>
                <CardTitle className="text-2xl">
                  {stats.by_type[type.value] || 0}
                </CardTitle>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      {/* Search & Filter Section */}
      <div className="mb-6 flex flex-col gap-4 px-6 md:flex-row md:items-center md:justify-between">
        <div className="flex-1 max-w-md">
          <SearchInput
            placeholder={t('agents.memory-search-placeholder')}
            value={searchQuery}
            onChange={handleSearch}
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <Select
            value={typeFilter}
            onValueChange={(value) => setTypeFilter(value as MemoryType | 'all')}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {MEMORY_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {t(type.label)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 rounded bg-red-100 px-6 py-2 text-red-800 dark:bg-red-900 dark:text-red-200">
          {error}
        </div>
      )}

      {/* Memory List */}
      <div className="flex-1 overflow-auto px-6 pb-6">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="border-t-primary h-8 w-8 animate-spin rounded-full border-4 border-gray-200"></div>
          </div>
        ) : displayedMemories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Brain className="mb-4 h-12 w-12 text-gray-400" />
            <p className="text-gray-500">{t('agents.memory-no-results')}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {displayedMemories.map((memory) => (
              <Card key={memory.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-1 text-xs font-medium ${getTypeColor(memory.memory_type)}`}
                      >
                        {getTypeLabel(memory.memory_type)}
                      </span>
                      {/* Importance indicator */}
                      <div className="flex items-center gap-1">
                        <div className="h-1.5 w-16 overflow-hidden rounded bg-gray-200">
                          <div
                            className="h-full bg-yellow-500 transition-all"
                            style={{ width: `${(memory.importance || 0.5) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400">
                          {Math.round((memory.importance || 0.5) * 100)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEditClick(memory)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteClick(memory)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap text-sm">
                    {memory.content}
                  </p>
                  <p className="mt-2 text-xs text-gray-500">
                    {t('agents.memory-created')}:{' '}
                    {new Date(memory.created_at).toLocaleString()}
                  </p>
                </CardContent>

                {/* Summary Section */}
                <div className="px-6 pb-4">
                  <MemorySummary memory={memory} />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Add Memory Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('agents.memory-add-new')}</DialogTitle>
            <DialogDescription>
              Add a new memory for your agents to remember.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t('agents.memory-type')}
              </label>
              <Select
                value={newType}
                onValueChange={(value) => setNewType(value as MemoryType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MEMORY_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {t(type.label)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t('agents.memory-content')}
              </label>
              <Textarea
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="Enter memory content..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
              {t('agents.memory-cancel')}
            </Button>
            <Button onClick={handleAddMemory} disabled={!newContent.trim()}>
              {t('agents.memory-save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('agents.memory-delete')}</DialogTitle>
            <DialogDescription>
              {t('agents.memory-delete-confirm')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              {t('agents.memory-cancel')}
            </Button>
            <Button variant="warning" onClick={handleDeleteConfirm}>
              {t('agents.memory-delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Memory Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Memory</DialogTitle>
            <DialogDescription>
              Update the memory content and type.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t('agents.memory-type')}
              </label>
              <Select
                value={editType}
                onValueChange={(value) => setEditType(value as MemoryType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MEMORY_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {t(type.label)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t('agents.memory-content')}
              </label>
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                placeholder="Enter memory content..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              {t('agents.memory-cancel')}
            </Button>
            <Button onClick={handleEditSave} disabled={!editContent.trim()}>
              {t('agents.memory-save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Memory Dialog */}
      <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Importar Memórias</DialogTitle>
            <DialogDescription>
              Cole o conteúdo JSON do backup para importar memórias.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Dados JSON</label>
              <Textarea
                value={importData}
                onChange={(e) => setImportData(e.target.value)}
                placeholder='[{"content": "...", "memory_type": "fact"}, ...]'
                rows={8}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setImportDialogOpen(false)}>
              {t('agents.memory-cancel')}
            </Button>
            <Button onClick={handleImport} disabled={!importData.trim()}>
              Importar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
          </TabsContent>

          {/* ========== TAB: ESTATÍSTICAS ========== */}
          <TabsContent value="stats">
            <div className="px-6 pb-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total de Memórias</CardDescription>
                    <CardTitle className="text-3xl">{stats?.total_memories ?? 0}</CardTitle>
                  </CardHeader>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Fatos</CardDescription>
                    <CardTitle className="text-3xl text-blue-600">{stats?.by_type?.fact ?? 0}</CardTitle>
                  </CardHeader>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Preferências</CardDescription>
                    <CardTitle className="text-3xl text-purple-600">{stats?.by_type?.preference ?? 0}</CardTitle>
                  </CardHeader>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Contexto</CardDescription>
                    <CardTitle className="text-3xl text-green-600">{stats?.by_type?.context ?? 0}</CardTitle>
                  </CardHeader>
                </Card>
              </div>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Distribuição por Tipo</CardTitle>
                  <CardDescription>Visão geral das categorias de memória</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex h-48 items-center justify-center">
                    <div className="flex w-full max-w-md flex-wrap justify-center gap-4">
                      {MEMORY_TYPES.map((type) => {
                        const count = stats?.by_type?.[type.value] ?? 0;
                        const total = stats?.total_memories ?? 1;
                        const percentage = Math.round((count / total) * 100);
                        return (
                          <div key={type.value} className="flex flex-col items-center">
                            <div
                              className="flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold"
                              style={{ backgroundColor: getTypeColor(type.value).split(' ')[0] }}
                            >
                              {percentage}%
                            </div>
                            <span className="mt-2 text-sm font-medium">{t(type.label)}</span>
                            <span className="text-xs text-gray-500">{count} memórias</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ========== TAB: CONFIGURAÇÕES ========== */}
          <TabsContent value="settings">
            <div className="space-y-6 px-6 pb-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Configurações de Memória
                  </CardTitle>
                  <CardDescription>
                    Gerencie como suas memórias são armazenadas e processadas
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Limite Máximo de Memórias</label>
                      <Select defaultValue="10000">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1000">1,000</SelectItem>
                          <SelectItem value="5000">5,000</SelectItem>
                          <SelectItem value="10000">10,000</SelectItem>
                          <SelectItem value="50000">50,000</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Dias de Retenção</label>
                      <Select defaultValue="90">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="30">30 dias</SelectItem>
                          <SelectItem value="60">60 dias</SelectItem>
                          <SelectItem value="90">90 dias</SelectItem>
                          <SelectItem value="180">180 dias</SelectItem>
                          <SelectItem value="365">365 dias</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Limiar de Sumarização</label>
                      <Select defaultValue="50">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="10">10 memórias</SelectItem>
                          <SelectItem value="25">25 memórias</SelectItem>
                          <SelectItem value="50">50 memórias</SelectItem>
                          <SelectItem value="100">100 memórias</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Criptografia</label>
                      <Select defaultValue="false">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="false">Desabilitada</SelectItem>
                          <SelectItem value="true">Habilitada</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4">
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="autoSummarize" defaultChecked className="rounded" />
                      <label htmlFor="autoSummarize" className="text-sm">
                        Sumarização automática após sessões
                      </label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="autoCleanup" defaultChecked className="rounded" />
                      <label htmlFor="autoCleanup" className="text-sm">
                        Limpeza automática de memórias antigas
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <KeyRound className="h-5 w-5" />
                    Criptografia
                  </CardTitle>
                  <CardDescription>
                    Proteja suas memórias sensíveis com criptografia
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Status: Desabilitada</p>
                      <p className="text-sm text-gray-500">Nenhuma memória criptografada</p>
                    </div>
                    <Button variant="outline">
                      <KeyRound className="mr-2 h-4 w-4" />
                      Configurar Criptografia
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ========== TAB: BACKUP ========== */}
          <TabsContent value="backup">
            <div className="space-y-6 px-6 pb-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Backup e Recuperação
                  </CardTitle>
                  <CardDescription>
                    Exporte e importe suas memórias
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="rounded-lg border p-4">
                      <h4 className="font-medium">Exportar Memórias</h4>
                      <p className="mb-4 text-sm text-gray-500">
                        Baixe todas as suas memórias em formato JSON
                      </p>
                      <Button className="w-full" onClick={handleExport} disabled={isLoading}>
                        <Database className="mr-2 h-4 w-4" />
                        Exportar JSON
                      </Button>
                    </div>
                    <div className="rounded-lg border p-4">
                      <h4 className="font-medium">Importar Memórias</h4>
                      <p className="mb-4 text-sm text-gray-500">
                        Restaure memórias de um backup anterior
                      </p>
                      <Button variant="outline" className="w-full" onClick={() => document.getElementById('import-file')?.click()} disabled={isLoading}>
                        <Database className="mr-2 h-4 w-4" />
                        Importar JSON
                      </Button>
                      <input
                        id="import-file"
                        type="file"
                        accept=".json"
                        className="hidden"
                        onChange={handleFileImport}
                      />
                    </div>
                  </div>

                  <div className="rounded-lg border p-4">
                    <h4 className="font-medium">Backup Automático</h4>
                    <p className="mb-4 text-sm text-gray-500">
                      Configure backups automáticos periódicos
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="autoBackup" defaultChecked className="rounded" />
                        <label htmlFor="autoBackup" className="text-sm">
                          Habilitar backup automático
                        </label>
                      </div>
                      <Select defaultValue="daily">
                        <SelectTrigger className="w-40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hourly">A cada hora</SelectItem>
                          <SelectItem value="daily">Diário</SelectItem>
                          <SelectItem value="weekly">Semanal</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
