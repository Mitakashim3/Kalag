import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, FileText, Search } from 'lucide-react'

const navItems = [
  { path: '/', label: 'Home', icon: LayoutDashboard },
  { path: '/documents', label: 'Docs', icon: FileText },
  { path: '/search', label: 'Search', icon: Search },
]

export default function MobileNav() {
  const location = useLocation()

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-background border-t safe-bottom z-40">
      <ul className="flex justify-around items-center h-16">
        {navItems.map(({ path, label, icon: Icon }) => (
          <li key={path}>
            <Link
              to={path}
              className={`flex flex-col items-center gap-1 px-4 py-2 transition-colors ${
                location.pathname === path
                  ? 'text-primary'
                  : 'text-muted-foreground'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs">{label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
