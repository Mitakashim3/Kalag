import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Lightbulb, Sparkles, FileText, HelpCircle, Search, Zap } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger)

export default function QuickTips() {
  const sectionRef = useRef<HTMLElement>(null)
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        cardRef.current,
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 90%', // Trigger earlier
            toggleActions: 'play none none reverse',
          },
        }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  const tips = [
    {
      icon: <FileText className="w-6 h-6 text-primary" />,
      title: 'Upload Rich PDFs',
      description: 'Kalag can read charts, tables, and images in your PDFs using advanced vision AI.',
    },
    {
      icon: <HelpCircle className="w-6 h-6 text-primary" />,
      title: 'Ask Specific Questions',
      description: 'Instead of "summarize", try "What was the Q3 revenue mentioned in the financial report?"',
    },
    {
      icon: <Search className="w-6 h-6 text-primary" />,
      title: 'Visual Citations',
      description: 'Every answer comes with visual citations showing exactly where the information was found.',
    },
    {
      icon: <Zap className="w-6 h-6 text-primary" />,
      title: 'Instant Answers',
      description: 'Get AI-powered responses in seconds, with full context from your documents.',
    },
  ]

  return (
    <section ref={sectionRef} className="py-20 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 pointer-events-none">
        <div 
          className="absolute top-1/4 -left-20 w-60 h-60 rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, hsl(var(--kalag-glow)) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
        />
        <div 
          className="absolute bottom-1/4 -right-20 w-80 h-80 rounded-full opacity-15"
          style={{
            background: 'radial-gradient(circle, hsl(var(--kalag-wisp)) 0%, transparent 70%)',
            filter: 'blur(80px)',
          }}
        />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <div 
          ref={cardRef}
          className="relative glass-panel rounded-3xl p-8 md:p-12 overflow-hidden"
        >
          {/* Decorative gradient bands */}
          <div className="absolute top-0 left-0 right-0 h-1 gradient-soul" />
          <div 
            className="absolute inset-0 opacity-30"
            style={{
              background: `
                linear-gradient(135deg, transparent 40%, hsl(var(--kalag-glow) / 0.1) 50%, transparent 60%)
              `,
            }}
          />

          {/* Header */}
          <div className="relative flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl gradient-soul flex items-center justify-center soul-glow">
              <Lightbulb className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                Quick Tips
                <Sparkles className="w-5 h-5 text-primary" />
              </h2>
              <p className="text-muted-foreground">Get the most out of Kalag</p>
            </div>
          </div>

          {/* Tips Grid */}
          <div className="relative grid md:grid-cols-2 gap-6">
            {tips.map((tip, i) => (
              <div 
                key={i}
                className="group flex gap-4 p-4 rounded-xl transition-all duration-300 hover:bg-muted/30"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                  {tip.icon}
                </div>
                <div>
                  <h3 className="font-semibold mb-1">{tip.title}</h3>
                  <p className="text-sm text-muted-foreground">{tip.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Floating orbs decoration */}
          <div className="absolute top-8 right-8 w-4 h-4 rounded-full bg-primary/40 wisp" />
          <div className="absolute bottom-12 right-20 w-3 h-3 rounded-full bg-primary/30 wisp" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 right-12 w-2 h-2 rounded-full bg-primary/50 wisp" style={{ animationDelay: '2s' }} />
        </div>
      </div>
    </section>
  )
}
