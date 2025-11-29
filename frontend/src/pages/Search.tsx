import { useState, useRef, useEffect, useMemo } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { Search as SearchIcon, Send, FileText, Image, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

// Component to load authenticated images
function AuthenticatedImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(false)

    api.get(src, { responseType: 'blob' })
      .then((response) => {
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

export default function Search() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [result, setResult] = useState<SearchResult | null>(null)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const markdownComponents = useMemo(
    () => ({
      p: ({ children }: { children?: React.ReactNode }) => (
        <p className="mb-3 leading-relaxed text-muted-foreground last:mb-0">{children}</p>
      ),
      strong: ({ children }: { children?: React.ReactNode }) => (
        <strong className="font-semibold text-foreground">{children}</strong>
      ),
      ul: ({ children }: { children?: React.ReactNode }) => (
        <ul className="mb-3 list-disc pl-5 text-muted-foreground space-y-1">{children}</ul>
      ),
      ol: ({ children }: { children?: React.ReactNode }) => (
        <ol className="mb-3 list-decimal pl-5 text-muted-foreground space-y-1">{children}</ol>
      ),
      li: ({ children }: { children?: React.ReactNode }) => (
        <li className="leading-relaxed">{children}</li>
      ),
      em: ({ children }: { children?: React.ReactNode }) => (
        <em className="text-foreground/80">{children}</em>
      ),
      code: ({ children }: { children?: React.ReactNode }) => (
        <code className="rounded bg-muted px-1 py-0.5 text-xs text-foreground">{children}</code>
      )
    }),
    []
  )

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!query.trim() || isSearching) return

    setIsSearching(true)
    setResult(null)
    setSelectedCitation(null)

    try {
      const response = await api.post('/api/search/', {
        query: query.trim(),
        include_images: true,
        top_k: 5,
      })
      setResult(response.data)
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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">Search Documents</h1>
        <p className="text-muted-foreground">
          Ask questions about your uploaded documents
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="relative">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question, e.g., 'What was the Q3 revenue?'"
          className="pl-10 pr-12 h-12 text-base"
          disabled={isSearching}
        />
        <Button
          type="submit"
          size="icon"
          className="absolute right-1 top-1/2 -translate-y-1/2"
          disabled={!query.trim() || isSearching}
        >
          {isSearching ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </form>

      {/* Loading State */}
      {isSearching && (
        <Card>
          <CardContent className="py-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary" />
            <p className="text-muted-foreground">Searching your documents...</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Answer */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Answer</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm space-y-2">
                <ReactMarkdown components={markdownComponents}>
                  {result.answer}
                </ReactMarkdown>
              </div>
              <p className="text-xs text-muted-foreground mt-4">
                Found in {result.processing_time_ms}ms
              </p>
            </CardContent>
          </Card>

          {/* Citations */}
          {result.citations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2">
                  {result.citations.map((citation, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedCitation(citation)}
                      className={`text-left p-3 rounded-lg border transition-colors ${
                        selectedCitation === citation
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-primary/50'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {citation.image_url ? (
                          <Image className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        ) : (
                          <FileText className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        )}
                        <div className="min-w-0">
                          <p className="font-medium text-sm truncate">
                            {citation.document_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Page {citation.page_number} • {Math.round(citation.relevance_score * 100)}% match
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Selected Citation Detail */}
          {selectedCitation && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  {selectedCitation.document_name} - Page {selectedCitation.page_number}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Page Image */}
                {selectedCitation.image_url && (
                  <div className="rounded-lg border overflow-hidden bg-muted">
                    <AuthenticatedImage
                      src={selectedCitation.image_url}
                      alt={`Page ${selectedCitation.page_number}`}
                      className="w-full h-auto"
                    />
                  </div>
                )}
                
                {/* Chunk Content */}
                <div>
                  <p className="text-sm font-medium mb-2">Relevant Text:</p>
                  <div className="text-sm text-muted-foreground bg-muted p-3 rounded-lg border space-y-2">
                    <ReactMarkdown components={markdownComponents}>
                      {selectedCitation.chunk_content}
                    </ReactMarkdown>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Empty State */}
      {!isSearching && !result && (
        <Card>
          <CardContent className="py-12 text-center">
            <SearchIcon className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-muted-foreground">
              Enter a question to search your documents
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Try: "What are the key findings?" or "Show me the revenue chart"
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
