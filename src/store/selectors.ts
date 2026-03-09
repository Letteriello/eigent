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

/**
 * Zustand Selectors - Optimized selectors for preventing unnecessary re-renders
 *
 * This module provides typed selectors for all Zustand stores to optimize
 * React component rendering. By selecting only the specific state needed,
 * components avoid re-rendering when unrelated state changes.
 */

import { shallow } from 'zustand/shallow';
import type { AuthState } from './authStore';
import type { ChatStore } from './chatStore';
import type { Project, ProjectStore } from './projectStore';

// ============================================================================
// ChatStore Selectors
// ============================================================================

/**
 * Select only the activeTaskId from chatStore
 * Use this when you only need to know which task is active
 */
export const selectActiveTaskId = (state: ChatStore) => state.activeTaskId;

/**
 * Select the entire tasks object
 * Use when you need to access multiple tasks
 */
export const selectTasks = (state: ChatStore) => state.tasks;

/**
 * Select a specific task by ID
 * Returns undefined if task doesn't exist
 */
export const selectTaskById = (taskId: string) => (state: ChatStore) =>
  state.tasks[taskId];

/**
 * Select task status for a specific task
 */
export const selectTaskStatus = (taskId: string) => (state: ChatStore) =>
  state.tasks[taskId]?.status;

/**
 * Select task messages for a specific task
 */
export const selectTaskMessages = (taskId: string) => (state: ChatStore) =>
  state.tasks[taskId]?.messages;

/**
 * Select task summary for a specific task
 */
export const selectTaskSummary = (taskId: string) => (state: ChatStore) =>
  state.tasks[taskId]?.summaryTask;

/**
 * Select active task object
 */
export const selectActiveTask = (state: ChatStore) => {
  const { activeTaskId, tasks } = state;
  if (!activeTaskId) return null;
  return tasks[activeTaskId] || null;
};

/**
 * Select the updateCount - useful for forcing updates
 */
export const selectUpdateCount = (state: ChatStore) => state.updateCount;

// ============================================================================
// AuthStore Selectors & Hooks
// ============================================================================

/**
 * Select authentication token
 */
export const selectToken = (state: AuthState) => state.token;

/**
 * Select user info (token, username, email, user_id)
 */
export const selectUserInfo = (state: AuthState) => ({
  token: state.token,
  username: state.username,
  email: state.email,
  user_id: state.user_id,
});

/**
 * Select appearance setting
 */
export const selectAppearance = (state: AuthState) => state.appearance;

/**
 * Select language setting
 */
export const selectLanguage = (state: AuthState) => state.language;

/**
 * Select model type settings
 */
export const selectModelSettings = (state: AuthState) => ({
  modelType: state.modelType,
  cloud_model_type: state.cloud_model_type,
});

/**
 * Select worker list for current user
 */
export const selectWorkerList = (state: AuthState) => {
  const email = state.email;
  if (!email) return [];
  return state.workerListData[email] || [];
};

// ============================================================================
// AuthStore Optimized Hooks (with shallow equality)
// ============================================================================

import { useAuthStore } from './authStore';

/**
 * Hook to get auth info (token, username, email, user_id)
 * Uses shallow equality to prevent unnecessary re-renders
 */
export const useAuthInfo = () =>
  useAuthStore(
    (state) => ({
      token: state.token,
      username: state.username,
      email: state.email,
      user_id: state.user_id,
    }),
    shallow
  );

/**
 * Hook to get app settings (appearance, language, isFirstLaunch)
 * Uses shallow equality to prevent unnecessary re-renders
 */
export const useAppSettings = () =>
  useAuthStore(
    (state) => ({
      appearance: state.appearance,
      language: state.language,
      isFirstLaunch: state.isFirstLaunch,
    }),
    shallow
  );

/**
 * Hook to get model preferences (modelType, cloud_model_type, preferredIDE)
 * Uses shallow equality to prevent unnecessary re-renders
 */
export const useModelPreferences = () =>
  useAuthStore(
    (state) => ({
      modelType: state.modelType,
      cloud_model_type: state.cloud_model_type,
      preferredIDE: state.preferredIDE,
    }),
    shallow
  );

/**
 * Hook to get init state
 * Uses shallow equality to prevent unnecessary re-renders
 */
export const useInitState = () => useAuthStore((state) => state.initState);

// ============================================================================
// ProjectStore Selectors
// ============================================================================

/**
 * Select active project ID
 */
export const selectActiveProjectId = (state: ProjectStore) =>
  state.activeProjectId;

/**
 * Select all projects
 */
export const selectAllProjects = (state: ProjectStore) => state.projects;

/**
 * Select a specific project by ID
 */
export const selectProjectById = (projectId: string) => (state: ProjectStore) =>
  state.projects[projectId] || null;

/**
 * Select active project
 */
export const selectActiveProject = (state: ProjectStore): Project | null => {
  const { activeProjectId, projects } = state;
  if (!activeProjectId) return null;
  return projects[activeProjectId] || null;
};

/**
 * Select active project ID with shallow comparison
 * Use this to prevent re-renders when other projects change
 */
export const selectActiveProjectIdShallow = (state: ProjectStore) =>
  state.activeProjectId;

// ============================================================================
// Utility Hooks with Shallow Equality
// ============================================================================

/**
 * Type for selector functions
 */
type Selector<TState, TSelected> = (state: TState) => TSelected;

/**
 * Create a selector that uses shallow equality
 * Use for arrays and objects to prevent unnecessary re-renders
 */
export function createShallowSelector<TState, TSelected>(
  selector: Selector<TState, TSelected>
): Selector<TState, TSelected> {
  return selector;
}

// ============================================================================
// Re-export shallow for external use
// ============================================================================

export { shallow };
