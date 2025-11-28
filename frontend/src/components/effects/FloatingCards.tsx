import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { FileText } from 'lucide-react'

export default function FloatingCards() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const cards = containerRef.current.querySelectorAll('.floating-card')

    cards.forEach((card, i) => {
      // Initial animation
      gsap.fromTo(
        card,
        { 
          opacity: 0, 
          y: 30,
          rotateY: -15,
        },
        { 
          opacity: 1, 
          y: 0,
          rotateY: -8 + i * 4,
          duration: 1.2,
          delay: 0.3 + i * 0.15,
          ease: 'power3.out'
        }
      )

      // Gentle floating animation
      gsap.to(card, {
        y: -8,
        duration: 3 + i * 0.5,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: i * 0.3,
      })
    })
  }, [])

  const handleMouseEnter = () => {
    if (!containerRef.current) return
    const cards = containerRef.current.querySelectorAll('.floating-card')
    
    // Scatter effect - Only animate X, Z and Rotation to avoid conflict with Y floating animation
    // Card 1 (Back) - Move further left/back
    gsap.to(cards[0], {
      x: -70, // Push out further
      z: -60,
      rotationY: -25,
      duration: 0.5,
      ease: 'back.out(1.7)'
    })

    // Card 2 (Middle) - Slight scale
    gsap.to(cards[1], {
      z: 10,
      scale: 1.05,
      rotationY: 0,
      duration: 0.5,
      ease: 'back.out(1.7)'
    })

    // Card 3 (Front) - Move further right/forward
    gsap.to(cards[2], {
      x: 70, // Push out further
      z: 60,
      rotationY: 25,
      duration: 0.5,
      ease: 'back.out(1.7)'
    })
  }

  const handleMouseLeave = () => {
    if (!containerRef.current) return
    const cards = containerRef.current.querySelectorAll('.floating-card')

    // Return to stacked state (matching the initial visual state)
    // Card 1
    gsap.to(cards[0], {
      x: -20, 
      z: -30, 
      rotationY: -8, // Match initial animation end state
      scale: 1,
      duration: 0.8,
      ease: 'power3.out'
    })

    // Card 2
    gsap.to(cards[1], {
      x: 0,
      z: 0,
      rotationY: -4, // Match initial animation end state
      scale: 1,
      duration: 0.8,
      ease: 'power3.out'
    })

    // Card 3
    gsap.to(cards[2], {
      x: 25, 
      z: 30, 
      rotationY: 0, // Match initial animation end state
      scale: 1,
      duration: 0.8,
      ease: 'power3.out'
    })
  }

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-72 perspective-1000 cursor-pointer"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Subtle glowing backdrop */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="w-48 h-48 rounded-full opacity-25"
          style={{
            background: 'radial-gradient(circle, hsl(var(--kalag-glow) / 0.4) 0%, transparent 70%)',
            filter: 'blur(50px)',
          }}
        />
      </div>

      {/* Simplified floating cards - stacked elegantly */}
      <div className="absolute inset-0 flex items-center justify-center preserve-3d">
        {/* Card 1 - Back */}
        <div 
          className="floating-card absolute w-44 h-56 rounded-2xl border border-primary/20 bg-card/40 backdrop-blur-md p-4"
          style={{ transform: 'translateZ(-30px) translateX(-20px) translateY(15px) rotateY(-5deg)' }}
        >
          <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center mb-3">
            <FileText className="w-4 h-4 text-primary/60" />
          </div>
          <div className="space-y-2">
            <div className="w-full h-2 bg-muted/40 rounded" />
            <div className="w-3/4 h-2 bg-muted/30 rounded" />
            <div className="w-5/6 h-2 bg-muted/20 rounded" />
          </div>
        </div>

        {/* Card 2 - Middle (Main) */}
        <div 
          className="floating-card absolute w-48 h-60 rounded-2xl border border-primary/30 bg-card/60 backdrop-blur-lg p-5 shadow-xl"
          style={{ 
            transform: 'translateZ(0px)',
            boxShadow: '0 0 40px hsl(var(--kalag-glow) / 0.15)'
          }}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl gradient-soul flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="w-16 h-2.5 bg-foreground/20 rounded mb-1" />
              <div className="w-12 h-2 bg-muted-foreground/30 rounded" />
            </div>
          </div>
          <div className="space-y-2 mb-4">
            <div className="w-full h-2 bg-muted/50 rounded" />
            <div className="w-4/5 h-2 bg-muted/40 rounded" />
            <div className="w-full h-2 bg-muted/30 rounded" />
          </div>
          <div className="w-full h-16 rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 border border-primary/20" />
        </div>

        {/* Card 3 - Front */}
        <div 
          className="floating-card absolute w-40 h-52 rounded-2xl border border-primary/20 bg-card/40 backdrop-blur-md p-4"
          style={{ transform: 'translateZ(30px) translateX(25px) translateY(-10px) rotateY(5deg)' }}
        >
          <div className="w-full h-12 rounded-lg bg-primary/10 mb-3 flex items-center justify-center">
            <div className="w-6 h-6 rounded-full bg-primary/25" />
          </div>
          <div className="space-y-2">
            <div className="w-full h-2 bg-muted/40 rounded" />
            <div className="w-2/3 h-2 bg-muted/30 rounded" />
            <div className="w-4/5 h-2 bg-muted/20 rounded" />
          </div>
        </div>
      </div>

      {/* Subtle floating orbs */}
      <div className="absolute top-16 right-16 w-3 h-3 rounded-full bg-primary/40 blur-sm wisp" />
      <div className="absolute bottom-24 left-16 w-2 h-2 rounded-full bg-primary/30 blur-sm wisp" style={{ animationDelay: '2s' }} />
    </div>
  )
}
