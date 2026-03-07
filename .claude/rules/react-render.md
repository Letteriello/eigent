---
paths:
  - src/**/*.tsx
---

# React Render Phase Rules

## Error: "Cannot update a component while rendering"

**Problem**: Calling state-modifying methods (like `createProject`, `setState`) during render phase causes React errors.

**Solution**:
1. Move side effects to `useEffect` (runs after render)
2. In Zustand stores, use `get()` inside methods to access state at call time, not definition time
3. Never call store actions during render - only in event handlers or useEffect

**Pattern**:
```tsx
// BAD - causes render error
const store = create((set, get) => ({
  init: () => {
    const state = get(); // This captures initial state!
    if (!state.user) set({ user: createUser() });
  }
}));

// GOOD - safe for useEffect
const store = create((set, get) => ({
  ensureUser: () => {
    const state = get(); // Gets current state at call time
    if (!state.user) set({ user: createUser() });
  }
}));

// Component
function MyComponent() {
  useEffect(() => {
    store.ensureUser(); // Called after render, not during
  }, []);
}
```
