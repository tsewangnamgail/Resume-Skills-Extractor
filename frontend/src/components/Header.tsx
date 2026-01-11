import { FileSearch, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
              <FileSearch className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">ResumeScreen</h1>
              <p className="text-xs text-muted-foreground">ATS Resume Analysis Dashboard</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
