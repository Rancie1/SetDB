# Zustand Explained - Complete Guide

## What is Zustand?

**Zustand** (German for "state") is a **lightweight state management library** for React. It's an alternative to Redux, Context API, or other state management solutions.

### Why Zustand?

1. **Simple**: Minimal boilerplate code
2. **Small**: Only ~1KB gzipped
3. **Fast**: No unnecessary re-renders
4. **TypeScript-friendly**: Great TypeScript support
5. **No Providers**: No need to wrap your app in providers
6. **Learning-friendly**: Easy to understand for beginners

### Comparison to Alternatives

| Feature | Zustand | Redux | Context API |
|---------|---------|-------|-------------|
| Boilerplate | Minimal | Lots | Medium |
| Bundle Size | ~1KB | ~10KB | Built-in |
| Learning Curve | Easy | Steep | Medium |
| Performance | Excellent | Good | Can be slow |
| DevTools | Optional | Excellent | None |

---

## Core Concepts

### 1. Store

A **store** is a container that holds your application state and functions to update it.

**Basic Structure:**
```javascript
import { create } from 'zustand';

const useStore = create((set, get) => ({
  // State (data)
  count: 0,
  name: 'John',
  
  // Actions (functions to update state)
  increment: () => set({ count: get().count + 1 }),
  setName: (name) => set({ name }),
}));
```

**Key Functions:**
- `set()` - Updates state (like React's `setState`)
- `get()` - Gets current state (useful in actions)

### 2. Using the Store in Components

```javascript
import useStore from './store';

function Counter() {
  // Get state and actions from store
  const { count, increment } = useStore();
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>Increment</button>
    </div>
  );
}
```

**That's it!** No providers, no connect, no hooks setup.

---

## How Zustand Works in Deckd

### Example 1: Auth Store (`store/authStore.js`)

Let's break down the auth store:

```javascript
const useAuthStore = create((set, get) => ({
  // ===== STATE =====
  user: JSON.parse(localStorage.getItem('user')) || null,
  token: localStorage.getItem('token') || null,
  loading: false,
  error: null,

  // ===== COMPUTED VALUES =====
  isAuthenticated: () => {
    return !!get().token && !!get().user;
  },

  // ===== ACTIONS =====
  login: async (email, password) => {
    set({ loading: true, error: null }); // Start loading
    try {
      const response = await authService.login(email, password);
      const { access_token } = response.data;
      
      // Get user info
      const userResponse = await authService.getCurrentUser();
      const user = userResponse.data;
      
      // Store in localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Update Zustand state
      set({
        token: access_token,
        user: user,
        loading: false,
        error: null,
      });
      
      return { success: true };
    } catch (error) {
      set({
        loading: false,
        error: errorMessage,
      });
      return { success: false, error: errorMessage };
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({
      user: null,
      token: null,
      error: null,
    });
  },
}));
```

**How to use it:**

```javascript
// In any component
import useAuthStore from '../store/authStore';

function LoginForm() {
  // Get what you need from the store
  const { login, loading, error } = useAuthStore();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(email, password);
    if (result.success) {
      // Redirect to home
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {error && <p>{error}</p>}
      <button disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

**In Header component:**
```javascript
function Header() {
  // Only get what you need - component only re-renders when these change
  const { user, logout, isAuthenticated } = useAuthStore();
  
  return (
    <header>
      {isAuthenticated() ? (
        <div>
          <p>Welcome, {user.username}!</p>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <Link to="/login">Login</Link>
      )}
    </header>
  );
}
```

### Example 2: Sets Store (`store/setsStore.js`)

```javascript
const useSetsStore = create((set, get) => ({
  // State
  sets: [],
  currentSet: null,
  filters: {
    search: '',
    source_type: null,
    dj_name: null,
  },
  loading: false,
  error: null,

  // Actions
  fetchSets: async (filters = {}, page = 1, limit = 20) => {
    set({ loading: true, error: null });
    try {
      // Merge new filters with existing
      const mergedFilters = { ...get().filters, ...filters };
      
      // Call API
      const response = await setsService.getSets(mergedFilters, page, limit);
      
      // Update state
      set({
        sets: response.data.items,
        filters: mergedFilters,
        loading: false,
      });
    } catch (error) {
      set({
        loading: false,
        error: error.message,
      });
    }
  },
}));
```

**Using it:**
```javascript
function SetsList() {
  const { sets, loading, fetchSets } = useSetsStore();
  
  useEffect(() => {
    fetchSets({ search: 'techno' }, 1, 20);
  }, []);
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      {sets.map(set => (
        <SetCard key={set.id} set={set} />
      ))}
    </div>
  );
}
```

---

## Key Zustand Features

### 1. Selective Subscriptions

**Problem with Context API:**
- If any value in context changes, ALL components re-render
- Can cause performance issues

**Zustand Solution:**
- Components only re-render when the values they use change
- Automatic optimization

```javascript
// Component only re-renders when 'user' changes
const { user } = useAuthStore();

// Component only re-renders when 'loading' changes
const { loading } = useAuthStore((state) => state.loading);

// Component re-renders when EITHER changes
const { user, loading } = useAuthStore();
```

### 2. No Provider Needed

**Redux/Context:**
```javascript
// Need to wrap app
<Provider store={store}>
  <App />
</Provider>
```

**Zustand:**
```javascript
// Just import and use!
const { user } = useAuthStore();
```

### 3. Async Actions

Zustand handles async actions naturally:

```javascript
login: async (email, password) => {
  set({ loading: true });
  try {
    const response = await api.login(email, password);
    set({ user: response.data, loading: false });
  } catch (error) {
    set({ error: error.message, loading: false });
  }
}
```

### 4. Accessing State in Actions

Use `get()` to read current state inside actions:

```javascript
increment: () => {
  const currentCount = get().count; // Get current value
  set({ count: currentCount + 1 }); // Update it
}
```

### 5. Computed Values

Functions that compute values from state:

```javascript
isAuthenticated: () => {
  return !!get().token && !!get().user;
}

// Usage
const { isAuthenticated } = useAuthStore();
if (isAuthenticated()) {
  // User is logged in
}
```

---

## Common Patterns in Deckd

### Pattern 1: Loading States

```javascript
// Store
const useStore = create((set) => ({
  loading: false,
  data: null,
  
  fetchData: async () => {
    set({ loading: true });
    try {
      const data = await api.getData();
      set({ data, loading: false });
    } catch (error) {
      set({ loading: false, error: error.message });
    }
  },
}));

// Component
function Component() {
  const { data, loading, fetchData } = useStore();
  
  if (loading) return <Spinner />;
  if (error) return <Error message={error} />;
  
  return <div>{data}</div>;
}
```

### Pattern 2: Error Handling

```javascript
// Store
const useStore = create((set) => ({
  error: null,
  
  clearError: () => set({ error: null }),
  
  action: async () => {
    try {
      await api.call();
      set({ error: null });
    } catch (error) {
      set({ error: error.message });
    }
  },
}));

// Component
function Component() {
  const { error, clearError } = useStore();
  
  return (
    <>
      {error && (
        <div>
          <p>{error}</p>
          <button onClick={clearError}>Dismiss</button>
        </div>
      )}
    </>
  );
}
```

### Pattern 3: LocalStorage Persistence

```javascript
// Initialize from localStorage
const useStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user')) || null,
  
  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user));
    set({ user });
  },
}));
```

---

## Advanced Usage

### Selecting Multiple Values Efficiently

```javascript
// Only re-renders when user OR token changes
const { user, token } = useAuthStore();

// More explicit selector (same behavior)
const user = useAuthStore((state) => state.user);
const token = useAuthStore((state) => state.token);
```

### Shallow Comparison

```javascript
// Only re-renders when filters object reference changes
const filters = useSetsStore((state) => state.filters);

// Better: Only re-renders when specific filter changes
const search = useSetsStore((state) => state.filters.search);
```

---

## When to Use Zustand vs Other Solutions

### Use Zustand When:
- ✅ You need global state
- ✅ Multiple components need the same data
- ✅ You want simple, minimal code
- ✅ You're learning state management

### Use Local State (useState) When:
- ✅ Only one component needs the data
- ✅ Data doesn't need to be shared
- ✅ Simple form inputs

### Use Props When:
- ✅ Passing data to child components
- ✅ Data flows down the component tree
- ✅ No need for global access

---

## Best Practices in Deckd

1. **One Store Per Domain**
   - `authStore.js` - Authentication
   - `setsStore.js` - DJ Sets
   - `uiStore.js` - UI state

2. **Keep Actions Simple**
   - One action = one responsibility
   - Handle errors in actions
   - Return success/error status

3. **Initialize from localStorage**
   - Restore state on page load
   - Persist important data

4. **Use Loading States**
   - Show spinners during async operations
   - Better user experience

5. **Clear Errors**
   - Provide `clearError` action
   - Let users dismiss error messages

---

## Summary

**Zustand is:**
- A simple state management library
- Perfect for React applications
- Easy to learn and use
- Performant and lightweight

**In Deckd, we use it for:**
- Authentication state (user, token)
- DJ sets data and filters
- UI state (modals, notifications)

**Key Takeaway:**
Zustand lets you manage global state without the complexity of Redux or the performance issues of Context API. It's the perfect middle ground!

