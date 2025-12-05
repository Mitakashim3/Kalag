import { useRef, useEffect, useState } from 'react'
import gsap from 'gsap'
import { useAuth } from '@/hooks/useAuth'
import { LayoutDashboard, FileText, Search, LogOut, ChevronDown } from 'lucide-react'

interface FloatingSidebarProps {
  onNavigate: (section: string) => void
  activeSection: string
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'search', label: 'Search', icon: Search },
]

export default function FloatingSidebar({ onNavigate, activeSection }: FloatingSidebarProps) {
  const { user, logout } = useAuth()
  const [isExpanded, setIsExpanded] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const chevronRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Initial animation
  useEffect(() => {
    if (sidebarRef.current) {
      gsap.fromTo(
        sidebarRef.current,
        { x: -20, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.6, ease: 'power3.out', delay: 0.2 }
      )
    }
  }, [])

  // Expand/collapse animation
  useEffect(() => {
    if (contentRef.current && chevronRef.current) {
      if (isExpanded) {
        gsap.to(contentRef.current, {
          height: 'auto',
          opacity: 1,
          duration: 0.4,
          ease: 'power2.out',
        })
        gsap.to(chevronRef.current, {
          rotate: 180,
          duration: 0.3,
          ease: 'power2.out',
        })
      } else {
        gsap.to(contentRef.current, {
          height: 0,
          opacity: 0,
          duration: 0.3,
          ease: 'power2.in',
        })
        gsap.to(chevronRef.current, {
          rotate: 0,
          duration: 0.3,
          ease: 'power2.in',
        })
      }
    }
  }, [isExpanded])

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsExpanded(true)
  }

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setIsExpanded(false)
    }, 300)
  }

  const handleNavigate = (section: string) => {
    onNavigate(section)
    setIsMobileOpen(false)
  }

  return (
    <>
      {/* Desktop Floating Sidebar */}
      <div
        ref={sidebarRef}
        className={`hidden md:block fixed left-6 top-6 z-50 transition-opacity duration-300 ${isExpanded ? 'opacity-100' : 'opacity-50 hover:opacity-100'}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="relative">
          {/* Main floating pill */}
          <div 
            className={`
              bg-card/90 backdrop-blur-xl border border-border/50 rounded-2xl shadow-xl
              transition-all duration-500 ease-out overflow-hidden
              ${isExpanded ? 'shadow-2xl' : 'hover:shadow-xl'}
            `}
            style={{
              boxShadow: isExpanded 
                ? '0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 30px hsl(var(--kalag-glow) / 0.1)'
                : '0 10px 40px -10px rgba(0, 0, 0, 0.15)'
            }}
          >
            {/* Logo Header - Always visible */}
            <div className="flex items-center gap-3 p-4 cursor-pointer">
              <div className="w-10 h-10 rounded-xl gradient-soul flex items-center justify-center shadow-lg p-1.5">
                <img src="/KalagLogo.svg" alt="Kalag" className="w-full h-full" />
              </div>
              <div className="flex-1">
                <span className="font-bold text-lg">Kalag</span>
              </div>
              <div 
                ref={chevronRef}
                className="w-6 h-6 rounded-lg bg-muted/50 flex items-center justify-center"
              >
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              </div>
            </div>

            {/* Expandable Content */}
            <div 
              ref={contentRef}
              className="overflow-hidden"
              style={{ height: 0, opacity: 0 }}
            >
              {/* Navigation */}
              <nav className="px-3 pb-2">
                <ul className="space-y-1">
                  {navItems.map(({ id, label, icon: Icon }) => (
                    <li key={id}>
                      <button
                        onClick={() => handleNavigate(id)}
                        className={`
                          w-full flex items-center gap-3 px-3 py-2.5 rounded-xl 
                          transition-all duration-200
                          ${activeSection === id
                            ? 'gradient-soul text-white shadow-md'
                            : 'hover:bg-muted/60 text-foreground/80 hover:text-foreground'
                          }
                        `}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="font-medium">{label}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </nav>

              {/* Divider */}
              <div className="mx-4 my-2 border-t border-border/50" />

              {/* User Section */}
              <div className="px-3 pb-3">
                <div className="flex items-center gap-3 p-2 rounded-xl bg-muted/30">
                  <div className="w-9 h-9 rounded-full gradient-soul flex items-center justify-center text-white text-sm font-medium">
                    {user?.full_name?.[0] || user?.email?.[0]?.toUpperCase() || 'C'}
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
                  className="w-full flex items-center gap-3 px-3 py-2.5 mt-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-200"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm">Sign Out</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-50 safe-top">
        <div className="m-4">
          <div 
            className="bg-card/90 backdrop-blur-xl border border-border/50 rounded-2xl shadow-lg"
            style={{ boxShadow: '0 10px 40px -10px rgba(0, 0, 0, 0.15)' }}
          >
            <div 
              className="flex items-center justify-between p-4 cursor-pointer"
              onClick={() => setIsMobileOpen(!isMobileOpen)}
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl gradient-soul flex items-center justify-center">
                  <span className="text-white font-bold">K</span>
                </div>
                <span className="font-bold text-lg">Kalag</span>
              </div>
              <div 
                className={`w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center transition-transform duration-300 ${isMobileOpen ? 'rotate-180' : ''}`}
              >
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              </div>
            </div>

            {/* Mobile Dropdown */}
            <div 
              className={`overflow-hidden transition-all duration-300 ${isMobileOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}
            >
              <nav className="px-3 pb-3">
                <ul className="space-y-1">
                  {navItems.map(({ id, label, icon: Icon }) => (
                    <li key={id}>
                      <button
                        onClick={() => handleNavigate(id)}
                        className={`
                          w-full flex items-center gap-3 px-3 py-3 rounded-xl 
                          transition-all duration-200
                          ${activeSection === id
                            ? 'gradient-soul text-white'
                            : 'hover:bg-muted/60'
                          }
                        `}
                      >
                        <Icon className="w-5 h-5" />
                        {label}
                      </button>
                    </li>
                  ))}
                </ul>

                <div className="mt-3 pt-3 border-t border-border/50">
                  <button
                    onClick={() => logout()}
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              </nav>
            </div>
          </div>
        </div>
      </header>
    </>
  )
}
