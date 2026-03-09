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

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useMemoryStore,
  useMemories,
  useMemoryStats,
  useMemoryStatus,
  type Memory,
  type MemoryStats,
} from '@/store/memoryStore';
import { Bot, Brain, RefreshCw, Search, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { MemoryCard } from './MemoryCard';

export function MemoryPanel() {
  const { t } = useTranslation();
  const memories = useMemories() as Memory[];
  const stats = useMemoryStats() as MemoryStats | null;
  const { isLoading, error } = useMemoryStatus() as { isLoading: boolean; error: string | null };
  const { fetchMemories, fetchStats, deleteMemory, searchMemories } =
    useMemoryStore();

  const [filterType, setFilterType] = useState<string>('all');
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchMemories();
    fetchStats();
  }, [fetchMemories, fetchStats]);

  const handleRefresh = async () => {
    await Promise.all([fetchMemories(), fetchStats()]);
    toast.success(t('memory-refreshed'));
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      await fetchMemories();
      return;
    }
    await searchMemories(searchQuery);
  };

  // Get unique agents from memories
  const agents = Array.from(
    new Set(memories.map((m) => m.agent_id).filter(Boolean))
  ) as string[];

  // Filter memories
  const filteredMemories = memories.filter((memory) => {
    if (filterType !== 'all' && memory.memory_type !== filterType) {
      return false;
    }
    if (filterAgent !== 'all' && memory.agent_id !== filterAgent) {
      return false;
    }
    return true;
  });

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          <h2 className="text-lg font-semibold">{t('memory-title')}</h2>
          <Badge variant="secondary">{memories.length}</Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isLoading}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`}
          />
          {t('common.refresh')}
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted p-3 text-sm md:grid-cols-4">
          <div>
            <span className="text-muted-foreground">
              {t('memory-stats-total')}:
            </span>{' '}
            <span className="font-medium">{stats.total_memories}</span>
          </div>
          {Object.entries(stats.by_type).map(([type, count]) => (
            <div key={type}>
              <span className="text-muted-foreground">{type}:</span>{' '}
              <span className="font-medium">{count}</span>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t('memory-search-placeholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="pl-9"
          />
        </div>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder={t('memory-filter-type')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('memory-filter-all')}</SelectItem>
            <SelectItem value="fact">{t('memory-fact')}</SelectItem>
            <SelectItem value="preference">
              {t('memory-preference')}
            </SelectItem>
            <SelectItem value="context">{t('memory-context')}</SelectItem>
            <SelectItem value="learned">{t('memory-learned')}</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterAgent} onValueChange={setFilterAgent}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder={t('memory-filter-agent')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('memory-filter-all')}</SelectItem>
            {agents.map((agent) => (
              <SelectItem key={agent} value={agent}>
                <div className="flex items-center gap-1">
                  <Bot className="h-3 w-3" />
                  {agent.slice(0, 8)}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-md bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20">
          <Trash2 className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Memory List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="flex h-32 flex-col items-center justify-center gap-2 text-muted-foreground">
            <Brain className="h-8 w-8" />
            <p>{t('memory-no-results')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredMemories.map((memory) => (
              <MemoryCard key={memory.id} memory={memory} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryPanel;
