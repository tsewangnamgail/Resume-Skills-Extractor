import { Briefcase, AlertTriangle } from 'lucide-react';
import { JobDescription } from '@/types/candidate';
import { Badge } from '@/components/ui/badge';

interface JobDescriptionCardProps {
  job: JobDescription;
}

export function JobDescriptionCard({ job }: JobDescriptionCardProps) {
  return (
    <div className="card-elevated p-6 animate-fade-in">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
          <Briefcase className="w-6 h-6 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl font-semibold text-foreground">{job.title}</h2>
            {job.min_experience_years !== undefined && (
              <Badge variant="secondary" className="text-xs font-medium">
                {job.min_experience_years}+ years exp
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm leading-relaxed mb-4">
            {job.description}
          </p>
          <div className="space-y-3">
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Mandatory Skills
              </h4>
              <div className="flex flex-wrap gap-2">
                {job.mandatory_skills?.map((skill) => (
                  <Badge key={skill} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
            {job.optional_skills && job.optional_skills.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Optional Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {job.optional_skills.map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs opacity-70">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
