import { useState, useRef, useEffect, useMemo } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { Search, Send, FileText, Image, Loader2, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

gsap.registerPlugin(ScrollTrigger)

// Authenticated Image Component
function AuthenticatedImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(false)

    api.get(src, { responseType: 'blob' })
      .then((response: { data: Blob }) => {
        if (mounted) {
          const url = URL.createObjectURL(response.data)
          setImageSrc(url)
          setLoading(false)
        }
      })
      .catch(() => {
        if (mounted) {
          setError(true)
          setLoading(false)
        }
      })

    return () => {
      mounted = false
      if (imageSrc) {
        URL.revokeObjectURL(imageSrc)
      }
    }
  }, [src])

  if (loading) {
    return (
      <div className={`flex items-center justify-center bg-muted ${className}`} style={{ minHeight: '200px' }}>
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !imageSrc) {
    return (
      <div className={`flex items-center justify-center bg-muted text-muted-foreground ${className}`} style={{ minHeight: '100px' }}>
        <p>Failed to load image</p>
      </div>
    )
  }

  return <img src={imageSrc} alt={alt} className={className} />
}

interface Citation {
  document_id: string
  document_name: string
  page_number: number
  chunk_content: string
  relevance_score: number
  image_url: string | null
}

interface SearchResult {
  answer: string
  citations: Citation[]
  query: string
  processing_time_ms: number
}

interface SearchSectionProps {
  autoFocus?: boolean
}

export default function SearchSection({ autoFocus }: SearchSectionProps) {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [result, setResult] = useState<SearchResult | null>(null)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const sectionRef = useRef<HTMLElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const sampleQueries = [
    'What are the key findings?',
    'Summarize the main points',
    'What was the Q3 revenue?',
    'Explain the methodology',
  ]

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        '.search-container',
        { y: 20, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: 'power3.out',
          // Removed ScrollTrigger to ensure it's always visible if the user scrolls fast or if trigger fails
          delay: 0.2
        }
      )
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [autoFocus])

  const handleSearch = async (searchQuery?: string) => {
    const q = searchQuery || query
    if (!q.trim()) return

    setIsSearching(true)
    setResult(null)
    setSelectedCitation(null)

    try {
      const response = await api.post('/api/search/', { query: q })
      setResult(response.data)
      
      // Animate results in
      gsap.fromTo(
        '.search-result',
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' }
      )
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Search Failed',
        description: error.response?.data?.detail || 'Could not complete search',
      })
    } finally {
      setIsSearching(false)
    }
  }

  const markdownComponents = useMemo(
    () => ({
      p: ({ children }: { children?: React.ReactNode }) => (
        <p className="mb-3 leading-relaxed text-foreground/80 last:mb-0">{children}</p>
      ),
      strong: ({ children }: { children?: React.ReactNode }) => (
        <strong className="font-semibold text-foreground">{children}</strong>
      ),
      ul: ({ children }: { children?: React.ReactNode }) => (
        <ul className="mb-3 list-disc pl-5 text-foreground/80 space-y-1">{children}</ul>
      ),
      ol: ({ children }: { children?: React.ReactNode }) => (
        <ol className="mb-3 list-decimal pl-5 text-foreground/80 space-y-1">{children}</ol>
      ),
      li: ({ children }: { children?: React.ReactNode }) => (
        <li className="leading-relaxed">{children}</li>
      ),
    }),
    []
  )

  return (
    <section ref={sectionRef} id="search" className="py-20 relative min-h-screen">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div 
          className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-96 rounded-full opacity-20"
          style={{
            background: 'radial-gradient(ellipse at center, hsl(var(--kalag-glow)) 0%, transparent 70%)',
            filter: 'blur(100px)',
          }}
        />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-panel text-sm mb-4">
            <Sparkles className="w-4 h-4 text-primary" />
            <span>AI-Powered Search</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Search Your Documents</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Ask questions in natural language and get instant answers with visual citations
          </p>
        </div>

        {/* Search Container */}
        <div className="search-container max-w-3xl mx-auto">
          {/* Search Input */}
          <div className="relative mb-6">
            <div className="absolute inset-0 rounded-2xl soul-glow opacity-50" />
            <div className="relative glass-panel rounded-2xl p-2">
              <div className="flex items-center gap-3">
                <div className="pl-4">
                  <Search className="w-5 h-5 text-muted-foreground" />
                </div>
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Ask anything about your documents..."
                  className="flex-1 py-4 bg-transparent border-none outline-none text-lg placeholder:text-muted-foreground/50"
                  disabled={isSearching}
                />
                <button
                  onClick={() => handleSearch()}
                  disabled={isSearching || !query.trim()}
                  className="p-4 rounded-xl gradient-soul text-white transition-all duration-300 hover:soul-glow disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSearching ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Sample Queries */}
          {!result && (
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              {sampleQueries.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuery(sq)
                    handleSearch(sq)
                  }}
                  className="px-4 py-2 rounded-full glass-panel text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-300"
                >
                  {sq}
                </button>
              ))}
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="search-result space-y-6">
              {/* Answer Card */}
              <div className="glass-panel rounded-2xl p-6 soul-glow">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-lg gradient-soul flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-semibold">Kalag's Answer</span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {result.processing_time_ms}ms
                  </span>
                </div>
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown components={markdownComponents}>
                    {result.answer}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Citations */}
              {result.citations.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    Sources ({result.citations.length})
                  </h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    {result.citations.map((citation, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedCitation(citation)}
                        className={`text-left glass-panel rounded-xl p-4 transition-all duration-300 hover:soul-glow ${
                          selectedCitation === citation ? 'ring-2 ring-primary' : ''
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                            {citation.image_url ? (
                              <Image className="w-5 h-5 text-muted-foreground" />
                            ) : (
                              <FileText className="w-5 h-5 text-muted-foreground" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-sm truncate">{citation.document_name}</p>
                            <p className="text-xs text-muted-foreground">Page {citation.page_number}</p>
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {citation.chunk_content}
                            </p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Citation Preview */}
              {selectedCitation?.image_url && (
                <div className="glass-panel rounded-2xl p-4 overflow-hidden">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold">Visual Citation</h4>
                    <button
                      onClick={() => setSelectedCitation(null)}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Close
                    </button>
                  </div>
                  <AuthenticatedImage
                    src={selectedCitation.image_url}
                    alt={`Page ${selectedCitation.page_number} from ${selectedCitation.document_name}`}
                    className="w-full rounded-lg"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
