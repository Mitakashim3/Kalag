import { useState, useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Loader2,
  ExternalLink,
  Trash2,
  RefreshCw
} from 'lucide-react'

gsap.registerPlugin(ScrollTrigger)

interface Document {
  id: string
  original_filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_pages: number | null
  file_size_bytes: number
  created_at: string
  processing_error: string | null
}

interface DocumentsSectionProps {
  refreshTrigger?: number
}

export default function DocumentsSection({ refreshTrigger }: DocumentsSectionProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [hoveredDoc, setHoveredDoc] = useState<string | null>(null)
  const sectionRef = useRef<HTMLElement>(null)
  const gridRef = useRef<HTMLDivElement>(null)
  const hasAnimatedRef = useRef(false)
  const { toast } = useToast()

  useEffect(() => {
    hasAnimatedRef.current = false
    fetchDocuments()
  }, [refreshTrigger])

  useEffect(() => {
    if (!isLoading && documents.length > 0 && gridRef.current && !hasAnimatedRef.current) {
      gsap.fromTo(
        gridRef.current.children,
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.5,
          stagger: 0.1,
          ease: 'power2.out',
        }
      )
      hasAnimatedRef.current = true
    }
  }, [isLoading, documents])

  // Auto-refresh document statuses while any are pending/processing.
  // This prevents the UI from staying "Pending" until a hard refresh.
  useEffect(() => {
    if (isLoading) return
    const hasInProgress = documents.some(
      (d) => d.status === 'pending' || d.status === 'processing'
    )
    if (!hasInProgress) return

    const interval = window.setInterval(() => {
      fetchDocuments({ silent: true })
    }, 3000)

    return () => window.clearInterval(interval)
  }, [isLoading, documents])

  const fetchDocuments = async (options?: { silent?: boolean }) => {
    try {
      const response = await api.get('/api/documents/')
      setDocuments(response.data.documents)
    } catch {
      if (!options?.silent) {
        toast({
          variant: 'destructive',
          title: 'Error',
          description: 'Failed to load documents',
        })
      }
    } finally {
      if (!options?.silent) {
        setIsLoading(false)
      }
    }
  }

  const deleteDocument = async (id: string) => {
    try {
      await api.delete(`/api/documents/${id}`)
      setDocuments(prev => prev.filter(d => d.id !== id))
      toast({
        title: 'Document Deleted',
        description: 'The document has been removed from your library',
      })
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete document',
      })
    }
  }

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-primary animate-spin" />
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
    }
  }

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return 'Ready'
      case 'processing':
        return 'Processing'
      case 'pending':
        return 'Pending'
      case 'failed':
        return 'Failed'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <section ref={sectionRef} id="documents" className="py-20 relative">
      {/* Background gradient */}
      <div className="absolute inset-0 pointer-events-none">
        <div 
          className="absolute bottom-0 left-0 right-0 h-96 opacity-30"
          style={{
            background: 'linear-gradient(to top, hsl(var(--kalag-glow) / 0.1) 0%, transparent 100%)',
          }}
        />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-2">Your Documents</h2>
            <p className="text-muted-foreground">
              {documents.length} document{documents.length !== 1 ? 's' : ''} in your library
            </p>
          </div>
          <button
            onClick={() => {
              setIsLoading(true)
              fetchDocuments()
            }}
            className="p-3 rounded-xl glass-panel hover:bg-muted/50 transition-colors"
            aria-label="Refresh documents"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <span className="text-muted-foreground">Loading documents...</span>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && documents.length === 0 && (
          <div className="text-center py-20">
            <div className="w-20 h-20 rounded-2xl glass-panel flex items-center justify-center mx-auto mb-6">
              <FileText className="w-10 h-10 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No Documents Yet</h3>
            <p className="text-muted-foreground mb-6">
              Upload your first PDF to start building your knowledge base
            </p>
          </div>
        )}

        {/* Documents Grid */}
        {!isLoading && documents.length > 0 && (
          <div ref={gridRef} className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="group relative glass-panel rounded-2xl p-5 transition-all duration-300 hover:soul-glow"
                onMouseEnter={() => setHoveredDoc(doc.id)}
                onMouseLeave={() => setHoveredDoc(null)}
              >
                {/* Document Icon & Info */}
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate" title={doc.original_filename}>
                      {doc.original_filename}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(doc.status)}
                      <span className="text-xs text-muted-foreground">
                        {getStatusText(doc.status)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Meta Info */}
                <div className="mt-4 pt-4 border-t border-border/50 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{doc.total_pages ? `${doc.total_pages} pages` : 'Processing...'}</span>
                  <span>{formatFileSize(doc.file_size_bytes)}</span>
                  <span>{formatDate(doc.created_at)}</span>
                </div>

                {/* Error Message */}
                {doc.status === 'failed' && doc.processing_error && (
                  <div className="mt-3 p-2 rounded-lg bg-red-500/10 text-red-500 text-xs">
                    {doc.processing_error}
                  </div>
                )}

                {/* Hover Overlay */}
                <div 
                  className={`absolute inset-0 rounded-2xl bg-background/90 backdrop-blur-sm flex items-center justify-center gap-3 transition-opacity duration-300 ${
                    hoveredDoc === doc.id ? 'opacity-100' : 'opacity-0 pointer-events-none'
                  }`}
                >
                  {doc.status === 'completed' && (
                    <button className="px-4 py-2 rounded-xl gradient-soul text-white text-sm font-medium flex items-center gap-2 hover:soul-glow transition-all">
                      <ExternalLink className="w-4 h-4" />
                      Open
                    </button>
                  )}
                  <button 
                    onClick={() => deleteDocument(doc.id)}
                    className="px-4 py-2 rounded-xl bg-red-500/10 text-red-500 text-sm font-medium flex items-center gap-2 hover:bg-red-500/20 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
