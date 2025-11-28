import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { FileText, Search, Upload } from 'lucide-react'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-2xl font-bold">
          Welcome back, {user?.full_name?.split(' ')[0] || 'User'}
        </h1>
        <p className="text-muted-foreground">
          Search your documents with AI-powered intelligence
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader>
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <Upload className="w-5 h-5 text-primary" />
            </div>
            <CardTitle className="text-lg">Upload Documents</CardTitle>
            <CardDescription>
              Add PDFs to your knowledge base
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/documents">
              <Button variant="outline" className="w-full">
                Upload PDF
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader>
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <Search className="w-5 h-5 text-primary" />
            </div>
            <CardTitle className="text-lg">Search Documents</CardTitle>
            <CardDescription>
              Ask questions about your files
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/search">
              <Button variant="outline" className="w-full">
                Start Searching
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader>
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <CardTitle className="text-lg">View Library</CardTitle>
            <CardDescription>
              Manage your uploaded documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/documents">
              <Button variant="outline" className="w-full">
                View All Docs
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Upload PDFs with charts and tables - Kalag can read visual content
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Ask specific questions like "What was the Q3 revenue in the financial report?"
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Get answers with visual citations showing the exact document section
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
