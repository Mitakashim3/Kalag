import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { useAuth } from '@/hooks/useAuth'
import ThemeToggle from '@/components/ui/ThemeToggle'
import FloatingCards from '@/components/effects/FloatingCards'
import SoulOrbs from '@/components/effects/SoulOrbs'

interface HeroSectionProps {
  onStartSearch: () => void
}

export default function HeroSection({ onStartSearch }: HeroSectionProps) {
  const { user } = useAuth()
  const sectionRef = useRef<HTMLElement>(null)
  const titleRef = useRef<HTMLHeadingElement>(null)
  const subtitleRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Animate title
      gsap.fromTo(
        titleRef.current,
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, delay: 0.3, ease: 'power3.out' }
      )

      // Animate subtitle
      gsap.fromTo(
        subtitleRef.current,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, delay: 0.5, ease: 'power3.out' }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section
      ref={sectionRef}
      id="dashboard"
      className="relative min-h-screen flex items-center py-20 md:py-0 overflow-hidden"
    >
      {/* Background Effects */}
      <SoulOrbs count={5} />
      
      {/* Gradient overlay */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse 70% 50% at 50% 0%, hsl(var(--kalag-glow) / 0.06) 0%, transparent 50%),
            radial-gradient(ellipse 50% 40% at 90% 90%, hsl(var(--kalag-wisp) / 0.04) 0%, transparent 50%)
          `,
        }}
      />

      <div className="container mx-auto px-6 lg:px-12 relative z-10 max-w-7xl">
        {/* Theme Toggle - Top Right */}
        <div className="fixed top-6 right-6 z-50">
          <ThemeToggle />
        </div>

        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center pt-20 md:pt-0">
          {/* Left Content */}
          <div className="space-y-6 lg:pl-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-card/60 backdrop-blur-sm border border-border/50 text-sm">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-muted-foreground">AI-Powered Intelligence</span>
            </div>

            <h1 
              ref={titleRef}
              className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight"
            >
              Welcome back,{' '}
              <span className="text-gradient-soul">
                {user?.full_name?.split(' ')[0] || 'Clark'}
              </span>
            </h1>

            <p 
              ref={subtitleRef}
              className="text-lg md:text-xl text-muted-foreground max-w-lg"
            >
              Search your documents with AI-powered intelligence. 
              Upload PDFs and let Kalag's spirit guide you to the answers you seek.
            </p>

            <div className="flex flex-wrap gap-4 pt-4">
              <button 
                onClick={onStartSearch}
                className="px-8 py-4 rounded-xl gradient-soul text-white font-medium transition-all duration-300 hover:shadow-lg hover:shadow-primary/25 hover:scale-[1.02]"
              >
                Start Searching
              </button>
              <button 
                onClick={() => document.getElementById('documents')?.scrollIntoView({ behavior: 'smooth' })}
                className="px-8 py-4 rounded-xl bg-card/60 backdrop-blur-sm border border-border/50 font-medium transition-all duration-300 hover:bg-card hover:border-primary/30"
              >
                View Documents
              </button>
            </div>

            {/* Stats */}
            <div className="flex gap-8 pt-8">
              <div>
                <p className="text-3xl font-bold text-primary">∞</p>
                <p className="text-sm text-muted-foreground">Questions Answered</p>
              </div>
              <div className="w-px bg-border" />
              <div>
                <p className="text-3xl font-bold text-primary">AI</p>
                <p className="text-sm text-muted-foreground">Powered Search</p>
              </div>
              <div className="w-px bg-border" />
              <div>
                <p className="text-3xl font-bold text-primary">PDF</p>
                <p className="text-sm text-muted-foreground">Vision Support</p>
              </div>
            </div>
          </div>

          {/* Right - Floating Cards Composition */}
          <div className="hidden lg:block">
            <FloatingCards />
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-60">
        <span className="text-xs text-muted-foreground">Scroll to explore</span>
        <div className="w-6 h-10 rounded-full border-2 border-muted-foreground/30 flex justify-center pt-2">
          <div className="w-1 h-2 rounded-full bg-muted-foreground/50 animate-bounce" />
        </div>
      </div>
    </section>
  )
}
