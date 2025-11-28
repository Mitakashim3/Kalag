import { useEffect, useRef } from 'react'
import gsap from 'gsap'

interface SoulOrbsProps {
  count?: number
}

export default function SoulOrbs({ count = 8 }: SoulOrbsProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const orbs = containerRef.current.querySelectorAll('.soul-orb')
    
    orbs.forEach((orb, i) => {
      // Random starting position animation
      gsap.set(orb, {
        x: Math.random() * 100 - 50,
        y: Math.random() * 100 - 50,
        scale: 0.5 + Math.random() * 0.5,
      })

      // Floating animation
      gsap.to(orb, {
        y: `+=${-30 - Math.random() * 40}`,
        x: `+=${Math.random() * 40 - 20}`,
        duration: 4 + Math.random() * 4,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: i * 0.3,
      })

      // Pulse animation
      gsap.to(orb, {
        scale: 0.8 + Math.random() * 0.4,
        opacity: 0.3 + Math.random() * 0.4,
        duration: 2 + Math.random() * 2,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: i * 0.2,
      })
    })
  }, [])

  const orbSizes = ['w-16 h-16', 'w-24 h-24', 'w-20 h-20', 'w-12 h-12', 'w-32 h-32', 'w-14 h-14', 'w-28 h-28', 'w-18 h-18']
  const positions = [
    'top-[10%] left-[5%]',
    'top-[20%] right-[10%]',
    'top-[40%] left-[15%]',
    'top-[60%] right-[5%]',
    'top-[70%] left-[8%]',
    'top-[30%] right-[20%]',
    'top-[80%] right-[15%]',
    'top-[15%] left-[25%]',
  ]

  return (
    <div 
      ref={containerRef} 
      className="absolute inset-0 overflow-hidden pointer-events-none"
      aria-hidden="true"
    >
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`soul-orb absolute ${orbSizes[i % orbSizes.length]} ${positions[i % positions.length]} rounded-full opacity-40`}
          style={{
            background: `radial-gradient(circle at 30% 30%, 
              hsl(var(--kalag-glow) / 0.6) 0%, 
              hsl(var(--kalag-wisp) / 0.3) 40%, 
              transparent 70%)`,
            filter: 'blur(8px)',
          }}
        />
      ))}
    </div>
  )
}
