# Deckd Frontend

React frontend for the Deckd DJ sets tracking application.

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Create a `.env` file** in the frontend directory:
   ```
   VITE_API_URL=http://localhost:8000/api
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000` (or the next available port)

## Project Structure

```
src/
├── components/     # Reusable UI components
│   ├── auth/      # Login, Register, ProtectedRoute
│   ├── layout/    # Header, Footer, Layout
│   ├── sets/      # SetCard, SetDetail, etc.
│   ├── reviews/   # Review components
│   ├── lists/     # List components
│   └── users/     # User components
├── pages/         # Page components
├── hooks/          # Custom React hooks
├── store/          # Zustand stores (state management)
├── services/       # API service functions
├── utils/          # Helper functions
└── App.jsx         # Main app with routing
```

## Tech Stack

- **React 19** - UI library
- **Vite** - Build tool
- **React Router v7** - Routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **React Hook Form** - Form handling

## Development

- `npm run dev` - Start dev server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
