import { useEffect, useRef } from 'react'
import gsap from 'gsap'

interface ParticleFieldProps {
  count?: number
  className?: string
}

export default function ParticleField({ count = 30, className = '' }: ParticleFieldProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const particles: HTMLDivElement[] = []

    // Create particles
    for (let i = 0; i < count; i++) {
      const particle = document.createElement('div')
      particle.className = 'absolute rounded-full'
      
      const size = Math.random() * 4 + 1
      particle.style.width = `${size}px`
      particle.style.height = `${size}px`
      particle.style.background = `hsl(var(--kalag-glow) / ${Math.random() * 0.3 + 0.1})`
      particle.style.left = `${Math.random() * 100}%`
      particle.style.top = `${Math.random() * 100}%`
      
      container.appendChild(particle)
      particles.push(particle)

      // Animate each particle
      gsap.to(particle, {
        y: `-=${50 + Math.random() * 100}`,
        x: `+=${Math.random() * 40 - 20}`,
        opacity: 0,
        duration: 3 + Math.random() * 4,
        repeat: -1,
        delay: Math.random() * 5,
        ease: 'power1.out',
        onRepeat: () => {
          gsap.set(particle, {
            y: 0,
            x: 0,
            opacity: Math.random() * 0.5 + 0.1,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          })
        },
      })
    }

    return () => {
      particles.forEach(p => {
        gsap.killTweensOf(p)
        p.remove()
      })
    }
  }, [count])

  return (
    <div 
      ref={containerRef} 
      className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}
      aria-hidden="true"
    />
  )
}
