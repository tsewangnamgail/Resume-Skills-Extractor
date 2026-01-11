import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Pencil, X, Plus } from 'lucide-react';
import { JobDescription } from '@/types/candidate';

interface JobDescriptionEditorProps {
  job: JobDescription;
  onSave: (job: JobDescription) => void;
}

export function JobDescriptionEditor({ job, onSave }: JobDescriptionEditorProps) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(job.title);
  const [description, setDescription] = useState(job.description);
  const [minExperience, setMinExperience] = useState(job.min_experience_years || 0);
  const [mandatorySkills, setMandatorySkills] = useState<string[]>(job.mandatory_skills || []);
  const [optionalSkills, setOptionalSkills] = useState<string[]>(job.optional_skills || []);
  const [newSkill, setNewSkill] = useState('');
  const [skillType, setSkillType] = useState<'mandatory' | 'optional'>('mandatory');

  const handleAddSkill = () => {
    if (newSkill.trim()) {
      if (skillType === 'mandatory' && !mandatorySkills.includes(newSkill.trim())) {
        setMandatorySkills([...mandatorySkills, newSkill.trim()]);
      } else if (skillType === 'optional' && !optionalSkills.includes(newSkill.trim())) {
        setOptionalSkills([...optionalSkills, newSkill.trim()]);
      }
      setNewSkill('');
    }
  };

  const handleRemoveSkill = (skill: string, type: 'mandatory' | 'optional') => {
    if (type === 'mandatory') {
      setMandatorySkills(mandatorySkills.filter((s) => s !== skill));
    } else {
      setOptionalSkills(optionalSkills.filter((s) => s !== skill));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSkill();
    }
  };

  const handleSave = () => {
    onSave({
      ...job,
      title,
      description,
      min_experience_years: minExperience,
      mandatory_skills: mandatorySkills,
      optional_skills: optionalSkills,
    });
    setOpen(false);
  };

  const handleCancel = () => {
    setTitle(job.title);
    setDescription(job.description);
    setMinExperience(job.min_experience_years || 0);
    setMandatorySkills(job.mandatory_skills || []);
    setOptionalSkills(job.optional_skills || []);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Pencil className="w-4 h-4" />
          Edit Job Description
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Job Description</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <Label htmlFor="title">Job Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Senior Backend Engineer"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="minExperience">Min Experience (Years)</Label>
            <Input
              id="minExperience"
              type="number"
              value={minExperience}
              onChange={(e) => setMinExperience(parseInt(e.target.value) || 0)}
              min={0}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Job Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the role and ideal candidate..."
              rows={6}
            />
          </div>

          <div className="space-y-2">
            <Label>Skills</Label>
            <div className="flex gap-2">
              <Select value={skillType} onValueChange={(value) => setSkillType(value as any)}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mandatory">Mandatory</SelectItem>
                  <SelectItem value="optional">Optional</SelectItem>
                </SelectContent>
              </Select>
              <Input
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Add a skill..."
                className="flex-1"
              />
              <Button type="button" onClick={handleAddSkill} size="icon" variant="secondary">
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-3 mt-4">
              {mandatorySkills.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold mb-2 uppercase text-muted-foreground">Mandatory</h4>
                  <div className="flex flex-wrap gap-2">
                    {mandatorySkills.map((skill) => (
                      <Badge key={skill} variant="secondary" className="gap-1 pr-1">
                        {skill}
                        <button onClick={() => handleRemoveSkill(skill, 'mandatory')} className="ml-1 rounded-full hover:bg-muted-foreground/20 p-0.5">
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {optionalSkills.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold mb-2 uppercase text-muted-foreground">Optional</h4>
                  <div className="flex flex-wrap gap-2">
                    {optionalSkills.map((skill) => (
                      <Badge key={skill} variant="outline" className="gap-1 pr-1">
                        {skill}
                        <button onClick={() => handleRemoveSkill(skill, 'optional')} className="ml-1 rounded-full hover:bg-muted-foreground/20 p-0.5">
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
