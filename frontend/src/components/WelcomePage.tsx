import { FileSearch, Users, GitCompare, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomePageProps {
  onStart: () => void;
}

export function WelcomePage({ onStart }: WelcomePageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex flex-col">
      {/* Header */}
      <header className="p-6">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
            <FileSearch className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold text-foreground">ResumeScreen</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-3xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8 animate-fade-in">
            <Sparkles className="w-4 h-4" />
            AI-Powered Recruitment Tool
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            AI Resume Screening
            <span className="block text-primary mt-2">System</span>
          </h1>

          {/* Description */}
          <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto mb-10 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            Analyze, compare, and manage candidate resumes efficiently. 
            Make data-driven hiring decisions with intelligent resume matching.
          </p>

          {/* CTA Button */}
          <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <Button 
              onClick={onStart}
              size="lg"
              className="text-lg px-8 py-6 rounded-xl bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-300 group"
            >
              Let's Begin
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 animate-fade-in" style={{ animationDelay: '0.4s' }}>
            <FeatureCard
              icon={<FileSearch className="w-6 h-6" />}
              title="Smart Analysis"
              description="AI-powered resume parsing and skill extraction"
            />
            <FeatureCard
              icon={<Users className="w-6 h-6" />}
              title="Candidate Ranking"
              description="Automatic scoring based on job requirements"
            />
            <FeatureCard
              icon={<GitCompare className="w-6 h-6" />}
              title="Easy Comparison"
              description="Side-by-side candidate comparison view"
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-sm text-muted-foreground">
        © 2024 ResumeScreen. Intelligent Hiring Made Simple.
      </footer>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="p-6 rounded-2xl bg-card border border-border hover:border-primary/30 hover:shadow-lg transition-all duration-300">
      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mx-auto mb-4">
        {icon}
      </div>
      <h3 className="font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}