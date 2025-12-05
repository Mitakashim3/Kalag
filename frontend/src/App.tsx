import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { Toaster } from './components/ui/toaster'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import KalagHome from './pages/KalagHome'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl gradient-soul flex items-center justify-center soul-glow animate-pulse p-2">
            <img src="/KalagLogo.svg" alt="Kalag" className="w-full h-full" />
          </div>
          <p className="text-muted-foreground">Loading Kalag...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/welcome" replace />
  }

  return <>{children}</>
}

// Redirect authenticated users away from public pages
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl gradient-soul flex items-center justify-center soul-glow animate-pulse p-2">
            <img src="/KalagLogo.svg" alt="Kalag" className="w-full h-full" />
          </div>
          <p className="text-muted-foreground">Loading Kalag...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/welcome" element={
          <PublicRoute>
            <Landing />
          </PublicRoute>
        } />
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/register" element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        } />

        {/* Protected single-page app */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <KalagHome />
            </ProtectedRoute>
          }
        />

        {/* Catch all - redirect to landing if not authenticated, home if authenticated */}
        <Route path="*" element={<Navigate to="/welcome" replace />} />
      </Routes>
      <Toaster />
    </>
  )
}

export default App
