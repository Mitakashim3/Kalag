import { Outlet } from 'react-router-dom'
import Header from './Header'
import MobileNav from './MobileNav'

export default function Layout() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header - hidden on mobile, visible on desktop */}
      <Header />
      
      {/* Main content area */}
      <main className="pb-16 md:pb-0 md:ml-64">
        <div className="container mx-auto px-4 py-6 max-w-5xl">
          <Outlet />
        </div>
      </main>
      
      {/* Mobile bottom navigation */}
      <MobileNav />
    </div>
  )
}
