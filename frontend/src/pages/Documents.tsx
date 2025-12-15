import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { 
  Upload, 
  FileText, 
  Trash2, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Loader2
} from 'lucide-react'

interface Document {
  id: string
  original_filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_pages: number | null
  file_size_bytes: number
  created_at: string
  processing_error: string | null
}

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const { toast } = useToast()

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/documents/')
      setDocuments(response.data.documents)
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load documents',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/api/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })

      setDocuments(prev => [response.data, ...prev])
      toast({
        title: 'Upload Started',
        description: 'Your document is being processed',
      })

      // Poll for status updates
      pollDocumentStatus(response.data.id)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Upload Failed',
        description: error.response?.data?.detail || 'Could not upload file',
      })
    } finally {
      setIsUploading(false)
    }
  }, [toast])

  const pollDocumentStatus = async (docId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/api/documents/${docId}`)
        const updatedDoc = response.data

        setDocuments(prev => 
          prev.map(d => d.id === docId ? updatedDoc : d)
        )

        if (updatedDoc.status === 'completed' || updatedDoc.status === 'failed') {
          clearInterval(interval)
          if (updatedDoc.status === 'completed') {
            toast({
              title: 'Processing Complete',
              description: `${updatedDoc.original_filename} is ready for search`,
            })
          }
        }
      } catch {
        clearInterval(interval)
      }
    }, 8000)
  }

  const handleDelete = async (docId: string) => {
    try {
      await api.delete(`/api/documents/${docId}`)
      setDocuments(prev => prev.filter(d => d.id !== docId))
      toast({
        title: 'Document Deleted',
        description: 'The document has been removed',
      })
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Could not delete document',
      })
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isUploading,
  })

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Documents</h1>
        <p className="text-muted-foreground">
          Upload and manage your PDF documents
        </p>
      </div>

      {/* Upload Area */}
      <Card>
        <CardContent className="pt-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
            } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-2">
              {isUploading ? (
                <Loader2 className="w-10 h-10 text-muted-foreground animate-spin" />
              ) : (
                <Upload className="w-10 h-10 text-muted-foreground" />
              )}
              <p className="text-sm text-muted-foreground">
                {isUploading 
                  ? 'Uploading...' 
                  : isDragActive 
                    ? 'Drop the PDF here' 
                    : 'Drag & drop a PDF, or click to select'}
              </p>
              <p className="text-xs text-muted-foreground">
                Maximum file size: 10MB
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>Your Documents</CardTitle>
          <CardDescription>
            {documents.length} document{documents.length !== 1 ? 's' : ''} uploaded
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No documents uploaded yet</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {documents.map((doc) => (
                <li
                  key={doc.id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="w-8 h-8 text-muted-foreground flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="font-medium truncate">{doc.original_filename}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {getStatusIcon(doc.status)}
                        <span className="capitalize">{doc.status}</span>
                        <span>•</span>
                        <span>{formatFileSize(doc.file_size_bytes)}</span>
                        {doc.total_pages && (
                          <>
                            <span>•</span>
                            <span>{doc.total_pages} pages</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(doc.id)}
                    className="flex-shrink-0 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
