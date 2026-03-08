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
import { Textarea } from '@/components/ui/textarea';
import {
  useMemoryStore,
  type Memory,
  type MemoryType,
} from '@/store/memoryStore';
import { Brain, Plus, Trash2 } from 'lucide-react';
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
    deleteMemory,
    searchMemories,
    fetchStats,
  } = useMemoryStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [memoryToDelete, setMemoryToDelete] = useState<Memory | null>(null);

  // Form state
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState<MemoryType>('fact');

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

  // Display memories (search results or all)
  const displayedMemories = useMemo(() => {
    if (searchQuery.trim() && searchResults.length > 0) {
      return searchResults;
    }
    return memories;
  }, [searchQuery, searchResults, memories]);

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
      <div className="flex w-full items-center justify-between px-6 pb-6 pt-8">
        <div className="text-heading-sm font-bold text-text-heading">
          {t('agents.memory')}
        </div>
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

      {/* Search Section */}
      <div className="mb-6 px-6">
        <SearchInput
          placeholder={t('agents.memory-search-placeholder')}
          value={searchQuery}
          onChange={handleSearch}
        />
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
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteClick(memory)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
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
    </div>
  );
}
