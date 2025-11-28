import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { useThemeStore } from '@/store/themeStore'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore()
  const buttonRef = useRef<HTMLButtonElement>(null)
  const iconRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (iconRef.current) {
      gsap.fromTo(
        iconRef.current,
        { rotate: -90, scale: 0.5, opacity: 0 },
        { rotate: 0, scale: 1, opacity: 1, duration: 0.4, ease: 'back.out(1.7)' }
      )
    }
  }, [theme])

  const handleToggle = () => {
    toggleTheme()
  }

  return (
    <button
      ref={buttonRef}
      onClick={handleToggle}
      className="relative w-11 h-11 rounded-xl bg-card/80 backdrop-blur-sm border border-border/50 flex items-center justify-center transition-all duration-300 hover:border-primary/50 hover:shadow-lg group"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      <div ref={iconRef} className="relative">
        {theme === 'light' ? (
          <Moon className="w-5 h-5 text-foreground/70 transition-colors group-hover:text-primary" />
        ) : (
          <Sun className="w-5 h-5 text-foreground/70 transition-colors group-hover:text-primary" />
        )}
      </div>
    </button>
  )
}
