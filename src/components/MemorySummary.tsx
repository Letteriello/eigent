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
  type MemorySummary as MemorySummaryType,
  type SummaryQuality,
} from '@/store/memoryStore';
import { ChevronDown, ChevronUp, Sparkles, Star, Zap } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface MemorySummaryProps {
  memory: Memory;
}

export default function MemorySummary({ memory }: MemorySummaryProps) {
  const { t } = useTranslation();
  const { summarizationStatus, summarizeMemory, getSummary } = useMemoryStore();

  const [expanded, setExpanded] = useState(false);

  const rawSummary = getSummary(memory.id) as any;
  const summary: MemorySummaryType = rawSummary as MemorySummaryType;
  const isSummarizing = summarizationStatus === 'summarizing';

  const handleSummarize = async () => {
    await summarizeMemory(memory.id);
  };

  const getQualityIcon = (quality: SummaryQuality) => {
    switch (quality) {
      case 'excellent':
        return <Star className="h-4 w-4 text-yellow-500" />;
      case 'good':
        return <Zap className="h-4 w-4 text-green-500" />;
      case 'partial':
        return <Sparkles className="h-4 w-4 text-blue-500" />;
    }
  };

  const getQualityColor = (quality: SummaryQuality) => {
    switch (quality) {
      case 'excellent':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'good':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'partial':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }
  };

  const getQualityLabel = (quality: SummaryQuality) => {
    switch (quality) {
      case 'excellent':
        return t('agents.summary-quality-excellent');
      case 'good':
        return t('agents.summary-quality-good');
      case 'partial':
        return t('agents.summary-quality-partial');
    }
  };

  return (
    <Card className="mt-4">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            <CardTitle className="text-sm">
              {t('agents.memory-summary')}
            </CardTitle>
          </div>
          {!summary && !isSummarizing && (
            <Button variant="outline" size="sm" onClick={handleSummarize}>
              <Sparkles className="mr-1 h-3 w-3" />
              {t('agents.summarize')}
            </Button>
          )}
          {isSummarizing && (
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600" />
              <span className="text-xs text-gray-500">
                {t('agents.summarizing')}
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {summary ? (
          <div className="space-y-3">
            {/* Quality Indicator */}
            <div className="flex items-center gap-2">
              {getQualityIcon(summary.quality)}
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${getQualityColor(summary.quality)}`}
              >
                {getQualityLabel(summary.quality)}
              </span>
              <span className="text-xs text-gray-500">
                {summary.sourceCount} {t('agents.summary-sources')}
              </span>
            </div>

            {/* Summary Content */}
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {String(summary.content)}
            </p>

            {/* Generated At */}
            <CardDescription className="text-xs">
              {t('agents.summary-generated')}:{' '}
              {new Date(summary.generatedAt).toLocaleString()}
            </CardDescription>

            {/* Expand Source Memories */}
            {memory.metadata?.sourceMemories && (
              <div className="mt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-xs"
                >
                  {expanded ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                  {expanded
                    ? t('agents.summary-hide-sources')
                    : t('agents.summary-show-sources')}
                </Button>

                {expanded && (
                  <div className="mt-2 space-y-2 rounded border p-3">
                    {(
                      memory.metadata.sourceMemories as MemorySummaryType[]
                    ).map((source, index) => (
                      <div
                        key={index}
                        className="rounded bg-gray-50 p-2 text-xs dark:bg-gray-800"
                      >
                        {source.content}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : !isSummarizing ? (
          <CardDescription className="text-sm">
            {t('agents.summary-no-summary')}
          </CardDescription>
        ) : null}
      </CardContent>
    </Card>
  );
}
