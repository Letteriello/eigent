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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  useMemoryStore,
  type Memory,
  type MemoryType,
  type ImportanceSource,
} from '@/store/memoryStore';
import { AlertTriangle, Bot, Clock, RefreshCw, Star, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';

interface MemoryCardProps {
  memory: Memory;
  onDelete?: (id: string) => void;
  onUpdate?: (id: string, updates: Partial<Memory>) => void;
}

export function MemoryCard({ memory, onDelete, onUpdate }: MemoryCardProps) {
  const { t } = useTranslation();
  const { deleteMemory, updateMemory } = useMemoryStore();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(memory.content);
  const [editedImportance, setEditedImportance] = useState(memory.importance);

  const handleDelete = async () => {
    if (!window.confirm(t('memory-delete-confirm'))) return;

    setIsDeleting(true);
    const success = await deleteMemory(memory.id);
    setIsDeleting(false);

    if (success) {
      toast.success(t('memory-deleted'));
      onDelete?.(memory.id);
    } else {
      toast.error(t('memory-delete-failed'));
    }
  };

  const handleSave = async () => {
    const success = await updateMemory(
      memory.id,
      editedContent,
      memory.memory_type,
      memory.metadata
    );

    if (success) {
      toast.success(t('memory-updated'));
      setIsEditing(false);
      onUpdate?.(memory.id, { content: editedContent });
    } else {
      toast.error(t('memory-update-failed'));
    }
  };

  const handleImportanceChange = async (importance: number) => {
    setEditedImportance(importance);
    const success = await updateMemory(
      memory.id,
      memory.content,
      memory.memory_type,
      { ...memory.metadata, importance, importance_source: 'manual' as ImportanceSource }
    );

    if (success) {
      onUpdate?.(memory.id, { importance, importance_source: 'manual' });
    }
  };

  const handleResetToAuto = async () => {
    const success = await updateMemory(
      memory.id,
      memory.content,
      memory.memory_type,
      { ...memory.metadata, importance: memory.importance, importance_source: 'auto' as ImportanceSource }
    );

    if (success) {
      toast.success(t('memory-reset-auto'));
      onUpdate?.(memory.id, { importance_source: 'auto' });
    }
  };

  const isAuto = memory.importance_source !== 'manual';

  const getTypeColor = (type: MemoryType): string => {
    switch (type) {
      case 'fact':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'preference':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'context':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'learned':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  const getTypeLabel = (type: MemoryType): string => {
    switch (type) {
      case 'fact':
        return t('memory-fact');
      case 'preference':
        return t('memory-preference');
      case 'context':
        return t('memory-context');
      case 'learned':
        return t('memory-learned');
      default:
        return type;
    }
  };

  return (
    <Card className="transition-all hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Badge className={getTypeColor(memory.memory_type)}>
              {getTypeLabel(memory.memory_type)}
            </Badge>
            <Badge variant={isAuto ? 'default' : 'secondary'}>
              {isAuto ? t('memory-auto') : t('memory-manual')}
            </Badge>
            {memory.agent_id && (
              <Badge variant="outline" className="gap-1">
                <Bot className="h-3 w-3" />
                {memory.agent_id.slice(0, 8)}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
              className="h-8 w-8 p-0"
            >
              <Star className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isEditing ? (
          <div className="space-y-3">
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {t('memory-importance')}:
              </span>
              <input
                type="range"
                min="0"
                max="10"
                value={editedImportance}
                onChange={(e) =>
                  handleImportanceChange(Number(e.target.value))
                }
                className="flex-1"
              />
              <span className="text-sm font-medium">{editedImportance}</span>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSave}>
                {t('common.save')}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setIsEditing(false);
                  setEditedContent(memory.content);
                  setEditedImportance(memory.importance);
                }}
              >
                {t('common.cancel')}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <CardTitle className="text-base font-normal">
              {memory.content}
            </CardTitle>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(memory.created_at).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <Star className="h-3 w-3" />
                {t('memory-importance')}: {memory.importance}
              </span>
              {!isAuto && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleResetToAuto}
                  className="h-6 gap-1 px-2 text-xs"
                >
                  <RefreshCw className="h-3 w-3" />
                  {t('memory-reset')}
                </Button>
              )}
            </div>
            {memory.last_recalled_at && (
              <div className="text-xs text-muted-foreground">
                {t('memory-last-recalled')}: {new Date(memory.last_recalled_at).toLocaleString()}
              </div>
            )}
            {memory.metadata && Object.keys(memory.metadata).length > 0 && (
              <CardDescription className="text-xs">
                {JSON.stringify(memory.metadata).slice(0, 100)}
                {JSON.stringify(memory.metadata).length > 100 && '...'}
              </CardDescription>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default MemoryCard;
