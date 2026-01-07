# Frontend Architecture - Detailed Explanation

## Overview

The Deckd frontend is a **Single Page Application (SPA)** built with React. It communicates with the FastAPI backend through REST API calls, manages state with Zustand, and uses React Router for navigation.

## Technology Stack

### Core Technologies
- **React 19.2.0** - UI library for building components
- **Vite 7.3.0** - Build tool and dev server (faster than Create React App)
- **React Router v7** - Client-side routing
- **Zustand 5.0.9** - State management (simpler than Redux)
- **Axios 1.13.2** - HTTP client for API calls
- **Tailwind CSS 3.4.19** - Utility-first CSS framework
- **React Hook Form 7.70.0** - Form handling and validation

### Why These Choices?
- **React**: Industry standard, huge ecosystem, component reusability
- **Vite**: Lightning-fast dev server, instant HMR (Hot Module Replacement)
- **Zustand**: Much simpler than Redux, less boilerplate, perfect for learning
- **Axios**: Better than fetch API, automatic JSON parsing, interceptors
- **Tailwind**: Rapid development, consistent design, responsive by default

## Project Structure

```
frontend/src/
├── components/          # Reusable UI components
│   ├── auth/           # Authentication components
│   │   ├── LoginForm.jsx
│   │   ├── RegisterForm.jsx
│   │   └── ProtectedRoute.jsx
│   ├── layout/         # Layout components
│   │   ├── Header.jsx
│   │   ├── Footer.jsx
│   │   └── Layout.jsx
│   ├── users/          # User-related components
│   │   ├── UserProfile.jsx
│   │   └── UserStats.jsx
│   ├── sets/           # DJ set components (to be built)
│   ├── reviews/         # Review components (to be built)
│   └── lists/          # List components (to be built)
├── pages/              # Page-level components
│   ├── HomePage.jsx
│   ├── LoginPage.jsx
│   ├── RegisterPage.jsx
│   ├── DiscoverPage.jsx
│   └── UserProfilePage.jsx
├── store/              # Zustand state stores
│   ├── authStore.js    # Authentication state
│   ├── setsStore.js    # DJ sets state
│   └── uiStore.js      # UI state (modals, notifications)
├── services/           # API service functions
│   ├── api.js          # Axios instance with interceptors
│   ├── authService.js  # Auth API calls
│   ├── setsService.js  # Sets API calls
│   └── usersService.js # Users API calls
├── utils/              # Helper functions
│   └── constants.js    # App constants
├── hooks/              # Custom React hooks (to be built)
├── App.jsx             # Main app component with routing
├── main.jsx            # Entry point
└── index.css           # Global styles (Tailwind imports)
```

## Architecture Layers

### 1. Entry Point (`main.jsx`)

**What it does:**
- Renders the React app into the DOM
- Wraps app in `StrictMode` for development warnings
- Imports global CSS (Tailwind)

**Code:**
```javascript
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

**Why StrictMode?**
- Detects potential problems
- Warns about deprecated APIs
- Helps identify side effects

---

### 2. App Component (`App.jsx`)

**What it does:**
- Sets up routing with React Router
- Checks authentication on app load
- Wraps all pages with Layout component
- Defines all routes

**Key Features:**

**Authentication Check:**
```javascript
useEffect(() => {
  checkAuth(); // Validates stored JWT token on app load
}, [checkAuth]);
```

**Routing:**
- Uses `BrowserRouter` for client-side routing
- Each route wrapped in `Layout` (Header + Footer)
- Protected routes use `ProtectedRoute` component
- Dynamic routes: `/users/:id`, `/sets/:id`

**Routes:**
- `/` - HomePage
- `/login` - LoginPage
- `/register` - RegisterPage
- `/discover` - DiscoverPage
- `/feed` - FeedPage (protected)
- `/users/:id` - UserProfilePage
- `/sets/:id` - SetDetailPage (placeholder)

---

### 3. State Management (Zustand Stores)

#### Auth Store (`store/authStore.js`)

**Purpose:** Manages user authentication state globally

**State:**
- `user` - Current user object (from localStorage)
- `token` - JWT token (from localStorage)
- `loading` - Loading state for async operations
- `error` - Error messages

**Actions:**
- `login(email, password)` - Authenticates user, stores token
- `register(userData)` - Creates new account
- `logout()` - Clears auth state and localStorage
- `checkAuth()` - Validates stored token on app load
- `updateUser(userData)` - Updates user profile
- `isAuthenticated()` - Returns boolean if user is logged in

**How it works:**
1. On login, stores token in localStorage
2. Token automatically added to API requests via interceptor
3. On app load, validates token with backend
4. If token invalid, clears state and redirects to login

**Example usage:**
```javascript
const { user, login, logout, isAuthenticated } = useAuthStore();
```

#### Sets Store (`store/setsStore.js`)

**Purpose:** Manages DJ sets data and filtering

**State:**
- `sets` - Array of DJ sets
- `currentSet` - Currently viewed set
- `filters` - Search/filter criteria
- `pagination` - Page info
- `loading` - Loading state
- `error` - Error messages

**Actions:**
- `fetchSets(filters, page, limit)` - Fetches sets with filters
- `fetchSet(id)` - Gets single set details
- `importSet(url)` - Imports set from YouTube/SoundCloud
- `clearError()` - Clears error state

#### UI Store (`store/uiStore.js`)

**Purpose:** Manages UI state (modals, notifications, theme)

**State:**
- `theme` - Light/dark mode
- `modalOpen` - Whether a modal is open
- `currentModal` - Which modal is open
- `notifications` - Array of notification messages

**Actions:**
- `toggleTheme()` - Switches light/dark mode
- `openModal(name)` - Opens a modal
- `closeModal()` - Closes current modal
- `showNotification(message, type)` - Shows toast notification

---

### 4. API Service Layer

#### Base API Client (`services/api.js`)

**What it does:**
- Creates Axios instance with base URL
- Adds JWT token to all requests automatically
- Handles 401 errors globally (redirects to login)

**Request Interceptor:**
```javascript
// Automatically adds token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

**Response Interceptor:**
```javascript
// Handles 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**Why interceptors?**
- **DRY principle**: Don't repeat token logic in every API call
- **Automatic**: Token added without thinking about it
- **Centralized error handling**: 401 handled in one place

#### Service Functions

Each service file contains functions for a specific resource:

**authService.js:**
- `login(email, password)` - POST to `/api/auth/login`
- `register(userData)` - POST to `/api/auth/register`
- `getCurrentUser()` - GET `/api/auth/me`

**setsService.js:**
- `getSets(filters, page, limit)` - GET `/api/sets`
- `getSet(id)` - GET `/api/sets/:id`
- `importSet(url, endpoint)` - POST `/api/sets/import/youtube` or `/soundcloud`

**usersService.js:**
- `getUser(id)` - GET `/api/users/:id`
- `getUserStats(id)` - GET `/api/users/:id/stats`
- `followUser(id)` - POST `/api/users/:id/follow`
- `unfollowUser(id)` - DELETE `/api/users/:id/follow`

**Pattern:**
- Each function is a thin wrapper around Axios
- Returns the Axios promise
- Components handle loading/error states

---

### 5. Components Architecture

#### Layout Components

**Layout.jsx:**
- Wraps all pages
- Provides consistent structure (Header + Footer)
- Handles main content area

**Header.jsx:**
- Navigation links (Home, Discover, Feed)
- User menu (Login/Register or Profile/Logout)
- Responsive design (mobile menu ready)
- Uses `useAuthStore` to check authentication
- Uses `useNavigate` for programmatic navigation

**Footer.jsx:**
- Simple footer with links and copyright

#### Authentication Components

**LoginForm.jsx:**
- Uses React Hook Form for form handling
- Validates email and password
- Shows/hides password toggle
- Calls `authStore.login()` on submit
- Displays error messages
- Redirects to home on success

**RegisterForm.jsx:**
- Validates: username, email, password, confirm password
- Password strength (min 8 characters)
- Password match validation
- Auto-login after registration
- Error handling

**ProtectedRoute.jsx:**
- Higher-order component wrapper
- Checks `isAuthenticated()` from auth store
- Shows loading state during check
- Redirects to `/login` if not authenticated
- Preserves intended destination

#### User Components

**UserProfile.jsx:**
- Fetches user data and stats on mount
- Displays profile header (avatar, username, bio)
- Shows statistics cards
- Tab navigation (Stats, Sets, Reviews, Lists)
- Follow/Unfollow button (if viewing other user)
- Edit Profile button (if own profile)
- Loading and error states

**UserStats.jsx:**
- Displays 6 statistics in grid
- Loading skeleton
- Responsive grid layout

---

### 6. Pages

**HomePage.jsx:**
- Landing page with hero section
- Feature cards
- Call-to-action buttons

**LoginPage.jsx:**
- Simple wrapper around LoginForm
- Centered layout

**RegisterPage.jsx:**
- Simple wrapper around RegisterForm
- Centered layout

**DiscoverPage.jsx:**
- Placeholder for browsing sets
- Will show sets list with filters

**UserProfilePage.jsx:**
- Wrapper around UserProfile component
- Gets user ID from URL params

---

### 7. Styling (Tailwind CSS)

**Configuration (`tailwind.config.js`):**
- Custom color palette (primary colors)
- Content paths (where to look for classes)
- Theme extensions

**Usage:**
- Utility classes: `bg-white`, `text-gray-900`, `rounded-lg`
- Responsive: `md:flex`, `lg:px-8`
- Hover states: `hover:bg-primary-700`
- Custom colors: `text-primary-600`

**Benefits:**
- Rapid development
- Consistent spacing/colors
- Responsive by default
- Small bundle size (only used classes included)

---

## Data Flow

### Example: User Login Flow

1. **User fills form** → `LoginForm.jsx`
2. **Form submits** → Calls `authStore.login(email, password)`
3. **Auth store** → Calls `authService.login()`
4. **Auth service** → Makes POST to `/api/auth/login` via `api.js`
5. **API interceptor** → Adds token to request (if exists)
6. **Backend** → Validates credentials, returns JWT token
7. **Auth service** → Returns response
8. **Auth store** → Stores token in localStorage, updates state
9. **Component** → Redirects to home page
10. **Header** → Updates to show "Profile" and "Logout" (reacts to state change)

### Example: Viewing User Profile

1. **User clicks profile link** → Navigates to `/users/:id`
2. **UserProfilePage** → Renders `UserProfile` component
3. **UserProfile** → Gets `id` from URL params (`useParams()`)
4. **useEffect** → Calls `loadUserData()` on mount
5. **loadUserData** → Calls `usersService.getUser(id)` and `getUserStats(id)`
6. **Service** → Makes API calls via `api.js`
7. **API interceptor** → Adds JWT token automatically
8. **Backend** → Returns user data and stats
9. **Component** → Updates state, re-renders with data
10. **UI** → Displays profile, stats, tabs

---

## Key Patterns

### 1. Container/Presentational Pattern
- **Pages** = Containers (fetch data, manage state)
- **Components** = Presentational (display data, handle UI)

### 2. Custom Hooks Pattern (Future)
- Extract reusable logic into hooks
- Example: `useAuth()`, `useSets()`, `useApi()`

### 3. Service Layer Pattern
- All API calls go through service functions
- Components don't directly use Axios
- Easy to mock for testing

### 4. Store Pattern (Zustand)
- Global state in stores
- Components subscribe to stores
- Actions update state, components react

---

## Environment Configuration

**`.env` file:**
```
VITE_API_URL=http://localhost:8000/api
```

**Why `VITE_` prefix?**
- Vite only exposes env vars prefixed with `VITE_` to the client
- Security: Prevents accidentally exposing secrets
- Access via: `import.meta.env.VITE_API_URL`

---

## Development Workflow

### Starting the App
```bash
cd frontend
npm run dev
```
- Starts Vite dev server (usually port 5173)
- Hot Module Replacement (HMR) - changes appear instantly
- Fast refresh - React components update without losing state

### Building for Production
```bash
npm run build
```
- Creates optimized bundle in `dist/` folder
- Minifies code
- Tree-shaking (removes unused code)
- Asset optimization

---

## Current State

### ✅ Completed
- Project setup and configuration
- Authentication system (login, register, logout)
- Routing setup
- Layout components (Header, Footer)
- User profile page with stats
- API service layer with interceptors
- State management (auth, sets, UI stores)
- Basic pages (Home, Login, Register, Discover, Profile)

### 🚧 To Be Built
- Set components (SetCard, SetDetail, SetList)
- Review components
- List components
- Search and filtering UI
- Feed page content
- Set detail page
- More pages and features

---

## Best Practices Used

1. **Separation of Concerns**
   - Services handle API calls
   - Stores manage state
   - Components handle UI

2. **Reusability**
   - Components are modular
   - Services can be used anywhere
   - Stores provide global state

3. **Error Handling**
   - Global error handling in API interceptor
   - Component-level error states
   - User-friendly error messages

4. **Loading States**
   - Loading indicators during API calls
   - Skeleton screens for better UX
   - Disabled buttons during operations

5. **Security**
   - JWT tokens stored securely
   - Automatic token refresh handling
   - Protected routes

---

## How Everything Connects

```
User Action
    ↓
Component (UI)
    ↓
Store Action (Zustand)
    ↓
Service Function (API call)
    ↓
Axios Instance (with interceptors)
    ↓
Backend API (FastAPI)
    ↓
Database (PostgreSQL)
    ↓
Response flows back up
    ↓
Store updates state
    ↓
Component re-renders
    ↓
UI updates
```

This architecture makes the app:
- **Maintainable**: Clear separation of concerns
- **Scalable**: Easy to add new features
- **Testable**: Each layer can be tested independently
- **Learnable**: Clear patterns, easy to understand

