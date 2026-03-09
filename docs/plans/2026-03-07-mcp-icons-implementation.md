# MCP Icons Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace placeholder green dots with real brand logos/icons for MCP tools (Discord, Slack, Gmail, etc.) in the IntegrationList and MCPListItem components.

**Architecture:** Create a centralized icon mapping library (mcpServiceIcons.tsx) with SVG components for each service, integrated into existing components that currently use placeholder icons.

**Tech Stack:** React, TypeScript, SVG inline components, Lucide icons (fallback)

---

### Task 1: Create mcpServiceIcons.tsx library

**Files:**

- Create: `src/lib/mcpServiceIcons.tsx`

**Step 1: Create the file with icon mapping**

```typescript
// src/lib/mcpServiceIcons.tsx
// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

import {
  type LucideIcon,
  Settings,
  Wrench,
  MessageSquare,
  Mail,
  Calendar,
  HardDrive,
  Link2,
  Github,
  Twitter,
  MessageCircle,
  Folder,
} from 'lucide-react';
import React from 'react';

// Discord SVG icon component
const DiscordIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
  </svg>
);

// Slack SVG icon component
const SlackIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
  </svg>
);

// Gmail SVG icon component
const GmailIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z"/>
  </svg>
);

// Notion SVG icon component
const NotionIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.98-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.84-.046.933-.56.933-1.167V6.354c0-.606-.233-.933-.746-.886l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.933-.234-1.495-.933l-4.577-7.186v6.952l1.448.327s0 .84-1.168.84l-3.22.186c-.094-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.454-.233 4.764 7.279v-6.44l-1.215-.14c-.093-.514.28-.886.747-.933zM2.1 1.155l13.589-.933c1.635-.14 2.055-.047 3.081.7l4.25 2.986c.7.513.933.653.933 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.921c0-.839.374-1.54 1.447-1.634z"/>
  </svg>
);

// LinkedIn SVG icon component
const LinkedInIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
  </svg>
);

// GitHub SVG icon component
const GitHubIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
  </svg>
);

// Twitter/X SVG icon component
const TwitterIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
  </svg>
);

// Google Drive SVG icon component
const DriveIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M7.71 3.5L1.15 15l3.43 6 6.56-10.5L7.71 3.5zm8.58 0l-6.57 10.5 3.43 6L19.7 9.5 16.29 3.5zm-3.43 7.5l3.43 6H24l-6.56-10.5-3.43 6z"/>
  </svg>
);

// Google Calendar SVG icon component
const CalendarIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11zM9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm-8 4H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/>
  </svg>
);

// Reddit SVG icon component
const RedditIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
  </svg>
);

// WhatsApp SVG icon component
const WhatsAppIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

// Lark/Feishu SVG icon component
const LarkIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M12.84 2.83H2.69a.63.63 0 0 0-.63.63v17a.63.63 0 0 0 .63.63h17a.63.63 0 0 0 .63-.63v-10.14a.63.63 0 0 0-.63-.63h-7.42zm-2.52 2.52h2.52v7.42h-2.52V5.35zm5.25 0h2.52a.63.63 0 0 1 .63.63v5.89a.63.63 0 0 1-.63.63h-2.52V5.35zm5.25 0h2.52a.63.63 0 0 1 .63.63v5.89a.63.63 0 0 1-.63.63h-2.52V5.35z"/>
  </svg>
);

// RAG/Documents SVG icon component
const RagIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/>
    <path d="M9 13h6v2H9zm0 4h6v2H9z"/>
  </svg>
);

// Search/EXA SVG icon component
const SearchIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 20,
  className = ''
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
  </svg>
);

// Map of service names to icons
const mcpServiceIconMap: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  // Discord
  'Discord': DiscordIcon,

  // Slack
  'Slack': SlackIcon,

  // Google
  'Gmail': GmailIcon,
  'Google Gmail Mcp Toolkit': GmailIcon,
  'Gmail Mcp Toolkit': GmailIcon,
  'Google Calendar': CalendarIcon,
  'Google Calendar Toolkit': CalendarIcon,
  'Google Drive': DriveIcon,
  'Google Drive Mcp Toolkit': DriveIcon,

  // Notion
  'Notion': NotionIcon,
  'Notion Toolkit': NotionIcon,
  'Notion Mcp Toolkit': NotionIcon,

  // LinkedIn
  'LinkedIn': LinkedInIcon,
  'Linked In Toolkit': LinkedInIcon,

  // GitHub
  'GitHub': GitHubIcon,
  'Github': GitHubIcon,
  'Github Toolkit': GitHubIcon,
  'Github Mcp Toolkit': GitHubIcon,

  // Twitter/X
  'Twitter': TwitterIcon,
  'X (Twitter)': TwitterIcon,
  'X(Twitter)': TwitterIcon,

  // Reddit
  'Reddit': RedditIcon,

  // WhatsApp
  'WhatsApp': WhatsAppIcon,
  'Whats App Toolkit': WhatsAppIcon,

  // Lark/Feishu
  'Lark': LarkIcon,
  'Feishu': LarkIcon,

  // RAG
  'RAG': RagIcon,

  // Search
  'Search': SearchIcon,
  'EXA Search': SearchIcon,
  'Search Toolkit': SearchIcon,
};

/**
 * Get the icon component for an MCP service
 * @param serviceName - The name of the MCP service
 * @returns React component for the service icon, or fallback icon if not found
 */
export function getMCPServiceIcon(
  serviceName: string,
  size: number = 20,
  className: string = ''
): React.ReactNode {
  // Try to find exact match first
  let Icon = mcpServiceIconMap[serviceName];

  // If not found, try case-insensitive match
  if (!Icon) {
    const lowerName = serviceName.toLowerCase();
    for (const [key, value] of Object.entries(mcpServiceIconMap)) {
      if (key.toLowerCase() === lowerName || key.toLowerCase().includes(lowerName) || lowerName.includes(key.toLowerCase())) {
        Icon = value;
        break;
      }
    }
  }

  // Fallback to generic icon
  if (!Icon) {
    Icon = Wrench;
  }

  return <Icon size={size} className={className} />;
}

export type { };
```

**Step 2: Commit**

Run: `git add src/lib/mcpServiceIcons.tsx && git commit -m "feat: add MCP service icons library with brand logos"`

---

### Task 2: Update IntegrationList component to use MCPServiceIcon

**Files:**

- Modify: `src/components/IntegrationList/index.tsx:1-50`
- Modify: `src/components/IntegrationList/index.tsx:340-380`

**Step 1: Add import for getMCPServiceIcon**

Add after line 23 (after TooltipSimple import):

```typescript
import { getMCPServiceIcon } from '@/lib/mcpServiceIcons';
```

**Step 2: Replace ellipse icon with MCPServiceIcon**

Find lines 345-354 (the isSelectMode section):

```typescript
// REPLACE this:
{(isSelectMode || showStatusDot) && (
  <img
    src={ellipseIcon}
    alt="icon"
    className="mr-2 h-3 w-3"
    style={{
      filter: isInstalled
        ? 'grayscale(0%) brightness(0) saturate(100%) invert(41%) sepia(99%) saturate(749%) hue-rotate(81deg) brightness(95%) contrast(92%)'
        : 'none',
    }}
  />
)}

// WITH this:
{(isSelectMode || showStatusDot) && (
  <div className="mr-2 flex-shrink-0">
    {getMCPServiceIcon(item.name, 20, isInstalled ? 'text-green-500' : 'text-gray-400')}
  </div>
)}
```

Find lines 366-377 (the manage mode section) and replace similarly:

```typescript
// REPLACE this:
{showStatusDot && (
  <img
    src={ellipseIcon}
    alt="icon"
    className="mr-2 h-3 w-3"
    style={{
      filter: isInstalled
        ? 'grayscale(0%) brightness(0) saturate(100%) invert(41%) sepia(99%) saturate(749%) hue-rotate(81deg) brightness(95%) contrast(92%)'
        : 'none',
    }}
  />
)}

// WITH this:
{showStatusDot && (
  <div className="mr-2 flex-shrink-0">
    {getMCPServiceIcon(item.name, 20, isInstalled ? 'text-green-500' : 'text-gray-400')}
  </div>
)}
```

**Step 3: Commit**

Run: `git add src/components/IntegrationList/index.tsx && git commit -m "feat: replace placeholder icons with brand logos in IntegrationList"`

---

### Task 3: Update MCPListItem component to use MCPServiceIcon

**Files:**

- Modify: `src/pages/Connectors/components/MCPListItem.tsx:1-50`

**Step 1: Add import for getMCPServiceIcon**

Add after line 20 (after types import):

```typescript
import { getMCPServiceIcon } from '@/lib/mcpServiceIcons';
```

**Step 2: Replace green dot with MCPServiceIcon**

Find line 42:

```typescript
// REPLACE this:
<div className="mx-xs h-3 w-3 bg-green-500 rounded-full"></div>

// WITH this:
<div className="mx-xs">
  {getMCPServiceIcon(item.mcp_name, 20, 'text-green-500')}
</div>
```

**Step 3: Commit**

Run: `git add src/pages/Connectors/components/MCPListItem.tsx && git commit -m "feat: replace status dot with brand icon in MCPListItem"`

---

### Task 4: Verify and test the changes

**Step 1: Run type check**

Run: `npm run type-check`
Expected: No TypeScript errors

**Step 2: Run lint**

Run: `npm run lint`
Expected: No linting errors (fix any that appear)

**Step 3: Run tests**

Run: `npm run test -- --run`
Expected: All tests pass

**Step 4: Commit**

Run: `git add -A && git commit -m "fix: type-check and lint fixes for MCP icons"`

---

### Task 5: Optional - Add more service icons if needed

If certain services are missing, add them to `mcpServiceIcons.tsx`:

- Check which services are available in `/api/config/info`
- Add SVG icons following the same pattern
- Commit each new addition

---

## Summary

| Task | Action                    | Files                                             |
| ---- | ------------------------- | ------------------------------------------------- |
| 1    | Create icon library       | `src/lib/mcpServiceIcons.tsx`                     |
| 2    | Update IntegrationList    | `src/components/IntegrationList/index.tsx`        |
| 3    | Update MCPListItem        | `src/pages/Connectors/components/MCPListItem.tsx` |
| 4    | Verify changes            | Type check, lint, tests                           |
| 5    | Add more icons (optional) | Extend `mcpServiceIcons.tsx`                      |

## Notes

- Icons use inline SVGs for brand accuracy
- Fallback to Lucide Wrench icon if service not found
- All icons support size and className props for styling
- Green color maintained for installed status indicator
