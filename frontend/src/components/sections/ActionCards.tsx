import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Upload, Search, FileText, X, Cloud, File } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

gsap.registerPlugin(ScrollTrigger)

interface ActionCardsProps {
  onSearch: () => void
  onDocuments: () => void
  onUploadSuccess?: () => void
}

export default function ActionCards({ onSearch, onDocuments, onUploadSuccess }: ActionCardsProps) {
  const [uploadOpen, setUploadOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const sectionRef = useRef<HTMLElement>(null)
  const cardsRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  useEffect(() => {
    const ctx = gsap.context(() => {
      if (cardsRef.current) {
        gsap.fromTo(
          cardsRef.current.children,
          { y: 40, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            stagger: 0.15,
            ease: 'power3.out',
            delay: 0.4 // Ensure it plays after hero animation
          }
        )
      }
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      await api.post('/api/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      toast({
        title: 'Upload Started',
        description: 'Your document is being processed by Kalag',
      })

      setUploadOpen(false)
      onUploadSuccess?.()
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Upload Failed',
        description: error.response?.data?.detail || 'Could not upload file',
      })
    } finally {
      setIsUploading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isUploading,
  })

  const actions = [
    {
      icon: Upload,
      title: 'Upload Documents',
      description: 'Add PDFs to your knowledge base for AI-powered search',
      buttonText: 'Upload PDF',
      onClick: () => setUploadOpen(true),
      gradient: 'from-emerald-500/20 to-teal-500/10',
    },
    {
      icon: Search,
      title: 'Search Documents',
      description: 'Ask questions and get AI-powered answers with citations',
      buttonText: 'Start Searching',
      onClick: onSearch,
      gradient: 'from-green-500/20 to-emerald-500/10',
    },
    {
      icon: FileText,
      title: 'View Library',
      description: 'Browse and manage your uploaded document collection',
      buttonText: 'View All Docs',
      onClick: onDocuments,
      gradient: 'from-teal-500/20 to-green-500/10',
    },
  ]

  return (
    <>
      <section ref={sectionRef} className="py-20 relative">
        {/* Section background */}
        <div className="absolute inset-0 gradient-soul-subtle opacity-50" />
        
        <div className="container mx-auto px-6 relative z-10">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Core Actions</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to build your AI-powered knowledge base
            </p>
          </div>

          <div ref={cardsRef} className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {actions.map((action, i) => (
              <div
                key={i}
                className="group relative card-ethereal glass-panel rounded-2xl p-6 cursor-pointer"
                onClick={action.onClick}
              >
                {/* Gradient overlay */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                
                {/* Icon */}
                <div className="relative z-10 w-14 h-14 rounded-xl gradient-soul flex items-center justify-center mb-4 group-hover:soul-glow transition-all duration-300">
                  <action.icon className="w-6 h-6 text-white" />
                </div>

                {/* Content */}
                <div className="relative z-10">
                  <h3 className="text-xl font-semibold mb-2">{action.title}</h3>
                  <p className="text-muted-foreground text-sm mb-4">{action.description}</p>
                  
                  <button className="w-full py-3 px-4 rounded-xl border border-border bg-background/50 font-medium transition-all duration-300 group-hover:border-primary group-hover:bg-primary/10">
                    {action.buttonText}
                  </button>
                </div>

                {/* Decorative corner glow */}
                <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-primary/10 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Upload Modal Overlay */}
      {uploadOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => !isUploading && setUploadOpen(false)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
          
          {/* Modal */}
          <div 
            className="relative w-full max-w-lg glass-panel rounded-2xl p-6 soul-glow"
            onClick={e => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => !isUploading && setUploadOpen(false)}
              className="absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center hover:bg-muted transition-colors"
              disabled={isUploading}
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-2xl gradient-soul flex items-center justify-center mx-auto mb-4 soul-glow">
                <Cloud className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold mb-2">Upload Document</h3>
              <p className="text-muted-foreground">
                Add a PDF to your Kalag knowledge base
              </p>
            </div>

            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer ${
                isDragActive 
                  ? 'border-primary bg-primary/10' 
                  : 'border-border hover:border-primary/50 hover:bg-muted/30'
              } ${isUploading ? 'pointer-events-none opacity-50' : ''}`}
            >
              <input {...getInputProps()} />
              
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mx-auto">
                  <File className="w-6 h-6 text-muted-foreground" />
                </div>
                
                {isDragActive ? (
                  <p className="text-primary font-medium">Drop your PDF here...</p>
                ) : (
                  <>
                    <p className="font-medium">
                      Drag & drop your PDF here
                    </p>
                    <p className="text-sm text-muted-foreground">
                      or click to browse files
                    </p>
                  </>
                )}
              </div>

              {isUploading && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/80 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="font-medium">Uploading...</span>
                  </div>
                </div>
              )}
            </div>

            <p className="text-xs text-muted-foreground text-center mt-4">
              Supported format: PDF • Max size: 50MB
            </p>
          </div>
        </div>
      )}
    </>
  )
}
