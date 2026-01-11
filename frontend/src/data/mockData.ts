import { Candidate, JobDescription } from '@/types/candidate';

export const mockJobDescription: JobDescription = {
  title: 'Senior Backend Engineer',
  description: 'We are looking for a Senior Backend Engineer to join our platform team. The ideal candidate will have strong experience in Python, API development, and cloud infrastructure.',
  mandatory_skills: ['Python', 'FastAPI', 'PostgreSQL', 'AWS', 'Docker', 'REST APIs', 'Microservices'],
  min_experience_years: 5,
  education_requirements: "Bachelor's degree in Computer Science or related field"
};

export const mockCandidates: Candidate[] = [
  {
    id: '1',
    name: 'Sarah Chen',
    roleLevel: 'Senior',
    scores: {
      skills_score: 95,
      experience_score: 90,
      education_score: 88,
      final_score: 92
    },
    matchedSkills: ['Python', 'FastAPI', 'PostgreSQL', 'AWS', 'Docker', 'REST APIs'],
    missingSkills: ['Microservices'],
    experienceSummary: '7 years of backend development experience with a focus on Python-based systems. Led API development at two major tech companies.',
    strengths: [
      'Strong backend experience aligned with job requirements',
      'Demonstrates relevant API development using FastAPI and Python',
      'Proven leadership in technical projects',
      'Extensive cloud deployment experience with AWS',
    ],
    weaknesses: [
      'Limited microservices architecture experience',
    ],
    confidenceNote: 'High confidence match based on direct skill alignment and relevant experience duration.',
    recommendation: 'Strong Fit',
  },
  {
    id: '2',
    name: 'Marcus Johnson',
    roleLevel: 'Mid',
    scores: {
      skills_score: 75,
      experience_score: 82,
      education_score: 80,
      final_score: 78
    },
    matchedSkills: ['Python', 'PostgreSQL', 'REST APIs', 'Docker'],
    missingSkills: ['FastAPI', 'AWS', 'Microservices'],
    experienceSummary: '5 years of software development with solid Python foundation. Experience with Django and Flask frameworks.',
    strengths: [
      'Solid Python programming foundation',
      'Good database experience with PostgreSQL',
      'Experience with containerization',
    ],
    weaknesses: [
      'No FastAPI experience (uses Django/Flask)',
      'Lacks cloud deployment experience (AWS, Docker)',
      'No microservices background',
    ],
    confidenceNote: 'Moderate confidence. Strong fundamentals but missing specific technology requirements.',
    recommendation: 'Partial Fit',
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    roleLevel: 'Senior',
    scores: {
      skills_score: 88,
      experience_score: 85,
      education_score: 82,
      final_score: 85
    },
    matchedSkills: ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Microservices'],
    missingSkills: ['AWS'],
    experienceSummary: '6 years building scalable backend systems. Strong microservices architecture experience using Python and FastAPI.',
    strengths: [
      'Excellent FastAPI and Python expertise',
      'Strong microservices architecture background',
      'Containerization and deployment experience',
    ],
    weaknesses: [
      'Lacks AWS experience (works primarily with GCP)',
    ],
    confidenceNote: 'Good match with transferable cloud skills. AWS can be learned quickly given GCP background.',
    recommendation: 'Strong Fit',
  },
  {
    id: '4',
    name: 'David Kim',
    roleLevel: 'Junior',
    scores: {
      skills_score: 60,
      experience_score: 68,
      education_score: 70,
      final_score: 65
    },
    matchedSkills: ['Python', 'PostgreSQL'],
    missingSkills: ['FastAPI', 'AWS', 'Docker', 'REST APIs', 'Microservices'],
    experienceSummary: '3 years of data engineering with Python scripting experience. Transitioning to backend development.',
    strengths: [
      'Strong Python scripting skills',
      'Database experience with SQL',
      'Eager learner with growth mindset',
    ],
    weaknesses: [
      'Limited backend API development experience',
      'No cloud infrastructure experience',
      'No containerization background',
      'Junior-level experience for senior role',
    ],
    confidenceNote: 'Below requirements for senior role. May be suitable for mid-level position with mentorship.',
    recommendation: 'Weak Fit',
  },
  {
    id: '5',
    name: 'Alexandra Petrov',
    roleLevel: 'Senior',
    scores: {
      skills_score: 90,
      experience_score: 88,
      education_score: 85,
      final_score: 88
    },
    matchedSkills: ['Python', 'FastAPI', 'AWS', 'Docker', 'REST APIs', 'Microservices'],
    missingSkills: ['PostgreSQL'],
    experienceSummary: '8 years of backend engineering. Expert in FastAPI and AWS. Uses MongoDB primarily but has SQL foundations.',
    strengths: [
      'Extensive backend engineering experience',
      'Expert-level AWS and FastAPI knowledge',
      'Strong microservices and containerization skills',
    ],
    weaknesses: [
      'Primarily uses MongoDB over PostgreSQL',
      'SQL skills may need refreshing',
    ],
    confidenceNote: 'Strong match. PostgreSQL gap is minor given general SQL understanding and willingness to adapt.',
    recommendation: 'Strong Fit',
  },
];
