import { useRef, useEffect } from 'react'
import gsap from 'gsap'
import { useAuth } from '@/hooks/useAuth'
import { LayoutDashboard, FileText, Search, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'

interface SidebarProps {
  onNavigate: (section: string) => void
  activeSection: string
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'search', label: 'Search', icon: Search },
]

export default function Sidebar({ onNavigate, activeSection }: SidebarProps) {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const sidebarRef = useRef<HTMLElement>(null)
  const logoRef = useRef<HTMLDivElement>(null)
  const navRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Animate sidebar on mount
      gsap.fromTo(
        sidebarRef.current,
        { x: -100, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.8, ease: 'power3.out' }
      )

      // Animate logo
      gsap.fromTo(
        logoRef.current,
        { scale: 0.8, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.6, delay: 0.2, ease: 'back.out(1.7)' }
      )

      // Stagger nav items
      if (navRef.current) {
        gsap.fromTo(
          navRef.current.children,
          { x: -20, opacity: 0 },
          { x: 0, opacity: 1, duration: 0.4, stagger: 0.1, delay: 0.4, ease: 'power2.out' }
        )
      }
    })

    return () => ctx.revert()
  }, [])

  const handleNavigate = (section: string) => {
    onNavigate(section)
    setMobileOpen(false)
  }

  return (
    <>
      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-50 glass-panel safe-top">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl gradient-soul flex items-center justify-center soul-glow">
              <span className="text-white font-bold text-lg">K</span>
            </div>
            <span className="font-semibold text-lg">Kalag</span>
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="w-10 h-10 rounded-lg flex items-center justify-center hover:bg-muted transition-colors"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Nav Overlay */}
      {mobileOpen && (
        <div 
          className="md:hidden fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Nav Panel */}
      <div className={`md:hidden fixed top-16 left-0 right-0 z-40 glass-panel transition-transform duration-300 ${mobileOpen ? 'translate-y-0' : '-translate-y-full'}`}>
        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map(({ id, label, icon: Icon }) => (
              <li key={id}>
                <button
                  onClick={() => handleNavigate(id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    activeSection === id
                      ? 'gradient-soul text-white soul-glow'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Desktop Sidebar */}
      <aside
        ref={sidebarRef}
        className="hidden md:flex fixed left-0 top-0 h-full w-72 flex-col glass-panel z-40"
      >
        {/* Logo */}
        <div ref={logoRef} className="p-6 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl gradient-soul flex items-center justify-center soul-glow">
              <span className="text-white font-bold text-xl">K</span>
            </div>
            <div>
              <span className="font-bold text-xl">Kalag</span>
              <p className="text-xs text-muted-foreground">AI Knowledge Base</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul ref={navRef} className="space-y-2">
            {navItems.map(({ id, label, icon: Icon }) => (
              <li key={id}>
                <button
                  onClick={() => handleNavigate(id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    activeSection === id
                      ? 'gradient-soul text-white soul-glow'
                      : 'hover:bg-muted/50 hover:translate-x-1'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-border/50">
          <div className="flex items-center gap-3 mb-4 p-3 rounded-xl bg-muted/30">
            <div className="w-10 h-10 rounded-full gradient-soul flex items-center justify-center text-white font-medium">
              {user?.full_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.full_name || 'Clark Jim A. Gabiota'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email || 'clark@example.com'}
              </p>
            </div>
          </div>
          <button
            onClick={() => logout()}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-300"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  )
}
