import { useState, useEffect, useCallback } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import FloatingSidebar from '@/components/layout/FloatingSidebar'
import HeroSection from '@/components/sections/HeroSection'
import ActionCards from '@/components/sections/ActionCards'
import QuickTips from '@/components/sections/QuickTips'
import SearchSection from '@/components/sections/SearchSection'
import DocumentsSection from '@/components/sections/DocumentsSection'

gsap.registerPlugin(ScrollTrigger)

export default function KalagHome() {
  const [activeSection, setActiveSection] = useState('dashboard')
  const [searchFocused, setSearchFocused] = useState(false)
  const [documentsRefresh, setDocumentsRefresh] = useState(0)

  useEffect(() => {
    // Setup scroll-based active section detection
    const sections = ['dashboard', 'search', 'documents']
    
    sections.forEach((sectionId) => {
      const element = document.getElementById(sectionId)
      if (element) {
        ScrollTrigger.create({
          trigger: element,
          start: 'top center',
          end: 'bottom center',
          onEnter: () => setActiveSection(sectionId),
          onEnterBack: () => setActiveSection(sectionId),
        })
      }
    })

    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill())
    }
  }, [])

  const handleNavigate = useCallback((section: string) => {
    const element = document.getElementById(section)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
    setActiveSection(section)
  }, [])

  const handleStartSearch = useCallback(() => {
    handleNavigate('search')
    setSearchFocused(true)
    // Reset focus trigger after navigation
    setTimeout(() => setSearchFocused(false), 1000)
  }, [handleNavigate])

  const handleUploadSuccess = useCallback(() => {
    setDocumentsRefresh(prev => prev + 1)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Floating Sidebar */}
      <FloatingSidebar onNavigate={handleNavigate} activeSection={activeSection} />

      {/* Main Content - Full width now */}
      <main>
        {/* Hero / Dashboard Section */}
        <HeroSection onStartSearch={handleStartSearch} />

        {/* Action Cards */}
        <ActionCards 
          onSearch={handleStartSearch} 
          onDocuments={() => handleNavigate('documents')}
          onUploadSuccess={handleUploadSuccess}
        />

        {/* Quick Tips */}
        <QuickTips />

        {/* Search Section */}
        <SearchSection autoFocus={searchFocused} />

        {/* Documents Section */}
        <DocumentsSection refreshTrigger={documentsRefresh} />

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
      </main>
    </div>
  )
}
