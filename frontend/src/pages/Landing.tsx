import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import ThemeToggle from '@/components/ui/ThemeToggle'
import gsap from 'gsap'
import { 
  FileText, 
  Search, 
  Shield, 
  Zap, 
  Eye, 
  EyeOff,
  ChevronRight,
  Sparkles,
  Lock,
  Users,
  BarChart3,
  ArrowRight,
  Check
} from 'lucide-react'

type AuthMode = 'login' | 'register'

export default function Landing() {
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  
  // Form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  
  const { login, register, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()
  
  // Refs for animations
  const heroRef = useRef<HTMLDivElement>(null)
  const featuresRef = useRef<HTMLDivElement>(null)
  const authRef = useRef<HTMLDivElement>(null)

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  // Animations
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Hero animations
      gsap.fromTo(
        '.hero-title',
        { y: 50, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, ease: 'power3.out' }
      )
      gsap.fromTo(
        '.hero-subtitle',
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 0.2, ease: 'power3.out' }
      )
      gsap.fromTo(
        '.hero-badge',
        { scale: 0.8, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.6, delay: 0.4, ease: 'back.out(1.7)' }
      )
      
      // Feature cards stagger
      gsap.fromTo(
        '.feature-card',
        { y: 40, opacity: 0 },
        { 
          y: 0, 
          opacity: 1, 
          duration: 0.6, 
          stagger: 0.1, 
          delay: 0.6,
          ease: 'power3.out' 
        }
      )
      
      // Auth panel
      gsap.fromTo(
        '.auth-panel',
        { x: 50, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.8, delay: 0.3, ease: 'power3.out' }
      )
    })

    return () => ctx.revert()
  }, [])

  // Reset form when switching modes
  useEffect(() => {
    setPassword('')
    setConfirmPassword('')
    setShowPassword(false)
    setShowConfirmPassword(false)
  }, [authMode])

  const validateForm = (): boolean => {
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      toast({
        variant: 'destructive',
        title: 'Invalid Email',
        description: 'Please enter a valid email address',
      })
      return false
    }

    // Password validation
    if (password.length < 8) {
      toast({
        variant: 'destructive',
        title: 'Password Too Short',
        description: 'Password must be at least 8 characters long',
      })
      return false
    }

    if (authMode === 'register') {
      // Check password strength
      const hasUpperCase = /[A-Z]/.test(password)
      const hasLowerCase = /[a-z]/.test(password)
      const hasNumber = /[0-9]/.test(password)
      
      if (!hasUpperCase || !hasLowerCase || !hasNumber) {
        toast({
          variant: 'destructive',
          title: 'Weak Password',
          description: 'Password must contain uppercase, lowercase, and numbers',
        })
        return false
      }

      if (password !== confirmPassword) {
        toast({
          variant: 'destructive',
          title: 'Passwords Don\'t Match',
          description: 'Please make sure both passwords are the same',
        })
        return false
      }

      if (fullName.trim().length < 2) {
        toast({
          variant: 'destructive',
          title: 'Name Required',
          description: 'Please enter your full name',
        })
        return false
      }
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return
    
    setIsLoading(true)

    try {
      if (authMode === 'login') {
        await login(email, password)
        // Navigation handled by useEffect
      } else {
        await register(email, password, fullName.trim())
        toast({
          title: 'Account Created!',
          description: 'Please sign in with your new account',
        })
        setAuthMode('login')
        setPassword('')
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || 
        (authMode === 'login' ? 'Invalid email or password' : 'Could not create account')
      toast({
        variant: 'destructive',
        title: authMode === 'login' ? 'Login Failed' : 'Registration Failed',
        description: message,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const features = [
    {
      icon: FileText,
      title: 'Smart Document Processing',
      description: 'Upload PDFs and let AI extract, analyze, and index your content automatically.',
    },
    {
      icon: Search,
      title: 'Semantic Search',
      description: 'Find information based on meaning, not just keywords. Ask questions naturally.',
    },
    {
      icon: Eye,
      title: 'Visual Citations',
      description: 'See exactly where answers come from with page images and highlighted sources.',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Your documents are encrypted, isolated, and never used for training.',
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Get answers in seconds with our optimized RAG pipeline and vector search.',
    },
    {
      icon: BarChart3,
      title: 'Rich Analytics',
      description: 'Understand your documents with AI-powered insights and summaries.',
    },
  ]

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Main gradient orbs */}
        <div 
          className="absolute top-0 left-1/4 w-[800px] h-[800px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, hsl(var(--kalag-glow)) 0%, transparent 60%)',
            filter: 'blur(100px)',
            transform: 'translate(-50%, -30%)',
          }}
        />
        <div 
          className="absolute bottom-0 right-0 w-[600px] h-[600px] rounded-full opacity-15"
          style={{
            background: 'radial-gradient(circle, hsl(var(--kalag-wisp)) 0%, transparent 60%)',
            filter: 'blur(80px)',
            transform: 'translate(30%, 30%)',
          }}
        />
        
        {/* Floating orbs */}
        <div className="absolute top-1/4 right-1/3 w-4 h-4 rounded-full bg-primary/30 animate-pulse" />
        <div className="absolute top-1/2 left-1/4 w-3 h-3 rounded-full bg-primary/20 animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-1/4 right-1/4 w-5 h-5 rounded-full bg-primary/25 animate-pulse" style={{ animationDelay: '2s' }} />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(hsl(var(--foreground)) 1px, transparent 1px),
              linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-background/80 border-b border-border/50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl gradient-soul flex items-center justify-center soul-glow p-1.5">
              <img src="/KalagLogo.svg" alt="Kalag" className="w-full h-full" />
            </div>
            <span className="font-bold text-xl">Kalag</span>
          </Link>
          
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setAuthMode('login')
                authRef.current?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              Sign In
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setAuthMode('register')
                authRef.current?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section ref={heroRef} className="pt-32 pb-20 px-6">
        <div className="container mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left: Hero Content */}
            <div className="space-y-8">
              <div className="hero-badge inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-sm">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-primary font-medium">AI-Powered Knowledge Base</span>
              </div>
              
              <h1 className="hero-title text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
                The Spirit of Your{' '}
                <span className="text-gradient-soul">Documents</span>
              </h1>
              
              <p className="hero-subtitle text-xl text-muted-foreground leading-relaxed max-w-lg">
                Upload your documents, ask questions in natural language, and get instant answers 
                with visual citations. Kalag understands your content deeply.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Button 
                  size="lg" 
                  className="gap-2"
                  onClick={() => {
                    setAuthMode('register')
                    authRef.current?.scrollIntoView({ behavior: 'smooth' })
                  }}
                >
                  Start Free <ArrowRight className="w-4 h-4" />
                </Button>
                <Button 
                  variant="outline" 
                  size="lg"
                  onClick={() => featuresRef.current?.scrollIntoView({ behavior: 'smooth' })}
                >
                  Learn More
                </Button>
              </div>
              
              {/* Trust badges */}
              <div className="flex items-center gap-6 pt-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Check className="w-4 h-4 text-primary" />
                  <span>No credit card required</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Check className="w-4 h-4 text-primary" />
                  <span>Enterprise-grade security</span>
                </div>
              </div>
            </div>

            {/* Right: Auth Panel */}
            <div ref={authRef} className="auth-panel relative">
              <div className="glass-panel rounded-3xl p-8 soul-glow">
                {/* Auth Toggle */}
                <div className="flex rounded-xl bg-muted/50 p-1 mb-8">
                  <button
                    onClick={() => setAuthMode('login')}
                    className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                      authMode === 'login'
                        ? 'bg-background shadow-sm text-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => setAuthMode('register')}
                    className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                      authMode === 'register'
                        ? 'bg-background shadow-sm text-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Create Account
                  </button>
                </div>

                {/* Form Header */}
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2">
                    {authMode === 'login' ? 'Welcome Back' : 'Get Started'}
                  </h2>
                  <p className="text-muted-foreground">
                    {authMode === 'login' 
                      ? 'Sign in to access your knowledge base' 
                      : 'Create your account in seconds'}
                  </p>
                </div>

                {/* Auth Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                  {authMode === 'register' && (
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input
                        id="fullName"
                        type="text"
                        placeholder="John Doe"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        required
                        disabled={isLoading}
                        className="h-11"
                        autoComplete="name"
                      />
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={isLoading}
                      className="h-11"
                      autoComplete="email"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={isLoading}
                        className="h-11 pr-10"
                        autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        tabIndex={-1}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {authMode === 'register' && (
                      <p className="text-xs text-muted-foreground">
                        Min 8 characters with uppercase, lowercase, and numbers
                      </p>
                    )}
                  </div>

                  {authMode === 'register' && (
                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">Confirm Password</Label>
                      <div className="relative">
                        <Input
                          id="confirmPassword"
                          type={showConfirmPassword ? 'text' : 'password'}
                          placeholder="••••••••"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          required
                          disabled={isLoading}
                          className="h-11 pr-10"
                          autoComplete="new-password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                          tabIndex={-1}
                        >
                          {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full h-11 mt-6"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>{authMode === 'login' ? 'Signing in...' : 'Creating account...'}</span>
                      </div>
                    ) : (
                      <span>{authMode === 'login' ? 'Sign In' : 'Create Account'}</span>
                    )}
                  </Button>
                </form>

                {/* Security notice */}
                <div className="mt-6 flex items-center justify-center gap-2 text-xs text-muted-foreground">
                  <Lock className="w-3 h-3" />
                  <span>Secured with enterprise-grade encryption</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section ref={featuresRef} className="py-24 px-6 relative">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need to{' '}
              <span className="text-gradient-soul">Unlock Knowledge</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Kalag combines cutting-edge AI with intuitive design to transform how you interact with documents.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <div
                key={idx}
                className="feature-card glass-panel rounded-2xl p-6 hover:soul-glow transition-all duration-300 group"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="container mx-auto max-w-4xl">
          <div className="glass-panel rounded-3xl p-12 text-center soul-glow relative overflow-hidden">
            {/* Background decoration */}
            <div 
              className="absolute inset-0 opacity-10"
              style={{
                background: 'radial-gradient(circle at 50% 50%, hsl(var(--kalag-glow)), transparent 70%)',
              }}
            />
            
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Transform Your Documents?
              </h2>
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                Join thousands of professionals who use Kalag to unlock insights from their documents.
              </p>
              <Button 
                size="lg" 
                className="gap-2"
                onClick={() => {
                  setAuthMode('register')
                  authRef.current?.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                Get Started Free <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-border/50">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg gradient-soul flex items-center justify-center p-1">
                <img src="/KalagLogo.svg" alt="Kalag" className="w-full h-full" />
              </div>
              <div>
                <span className="font-semibold">Kalag</span>
                <p className="text-xs text-muted-foreground">AI-Powered Knowledge Base</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} Kalag. The spirit of your documents.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
