import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, X, FileText, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/services/api';
import { StrictEvaluationResponse } from '@/types/candidate';

interface ResumeFile {
  id: string;
  file: File;
  isProcessing: boolean;
  error?: string;
  result?: StrictEvaluationResponse;
}

interface ResumeUploadProps {
  onAnalyzeResults: (results: StrictEvaluationResponse[]) => void;
  jdText: string;
  jobId?: string;
}

export function ResumeUpload({ onAnalyzeResults, jdText, jobId }: ResumeUploadProps) {
  const [files, setFiles] = useState<ResumeFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    const newFiles: ResumeFile[] = [];
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        toast.error(`${file.name} is not a PDF file`);
        continue;
      }

      newFiles.push({
        id: Math.random().toString(36).substr(2, 9),
        file,
        isProcessing: false,
      });
    }

    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      toast.error('Please select at least one PDF resume');
      return;
    }

    if (!jdText || jdText.trim().length < 10) {
      toast.error('Please provide a valid job description first');
      return;
    }

    setIsUploading(true);
    const results: StrictEvaluationResponse[] = [];
    const updatedFiles = [...files];

    for (let i = 0; i < updatedFiles.length; i++) {
      const fileItem = updatedFiles[i];
      if (fileItem.result) continue; // Skip already processed

      updatedFiles[i] = { ...fileItem, isProcessing: true, error: undefined };
      setFiles([...updatedFiles]);

      try {
        const result = await apiService.analyzeResume(fileItem.file, jdText, jobId);
        results.push(result);
        updatedFiles[i] = { ...fileItem, isProcessing: false, result };
      } catch (error) {
        console.error(error);
        updatedFiles[i] = { ...fileItem, isProcessing: false, error: error instanceof Error ? error.message : 'Analysis failed' };
      }
      setFiles([...updatedFiles]);
    }

    if (results.length > 0) {
      onAnalyzeResults(results);
      toast.success(`Successfully analyzed ${results.length} resume(s)`);
      // Remove successfully processed files
      setFiles(prev => prev.filter(f => !f.result));
    }

    setIsUploading(false);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Upload className="w-5 h-5 text-primary" />
          Upload & Analyze Resumes
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/50 transition-colors">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="application/pdf"
            onChange={handleFileInputChange}
            className="hidden"
            id="resume-upload-input"
          />
          <label
            htmlFor="resume-upload-input"
            className="cursor-pointer flex flex-col items-center gap-2"
          >
            <Upload className="w-8 h-8 text-muted-foreground" />
            <div>
              <span className="text-sm font-medium text-foreground">
                Click to upload PDF resume files
              </span>
              <p className="text-xs text-muted-foreground mt-1">
                Only PDF files are accepted. Multiple files supported.
              </p>
            </div>
          </label>
        </div>

        {files.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-foreground">
              Selected Files ({files.length})
            </div>
            {files.map((fileItem) => (
              <div
                key={fileItem.id}
                className="p-3 border rounded-lg space-y-2 relative bg-muted/20"
              >
                {!isUploading && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2 h-6 w-6 text-muted-foreground hover:text-destructive"
                    onClick={() => removeFile(fileItem.id)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}

                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-primary" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-xs text-foreground truncate">
                      {fileItem.file.name}
                    </div>
                  </div>
                  {fileItem.isProcessing && (
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  )}
                </div>

                {fileItem.error && (
                  <div className="text-[10px] text-destructive bg-destructive/10 p-1 rounded">
                    {fileItem.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {files.length > 0 && (
          <Button
            onClick={handleSubmit}
            disabled={isUploading}
            className="w-full gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              `Analyze ${files.length} Resume(s)`
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}