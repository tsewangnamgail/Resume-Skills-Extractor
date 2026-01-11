"""
utils.py - Helper utilities
"""

import re
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return f"JD-{uuid.uuid4().hex[:8].upper()}"


def generate_candidate_id() -> str:
    """Generate a unique candidate ID."""
    return f"CAND-{uuid.uuid4().hex[:8].upper()}"


def hash_text(text: str) -> str:
    """Generate a hash of text content."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return text.strip()


def extract_email(text: str) -> Optional[str]:
    """Extract email from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_years_of_experience(text: str) -> Optional[int]:
    """Extract years of experience from text."""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
        r'experience\s*[:of]?\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    
    return None


def parse_date_range(text: str) -> Dict[str, Any]:
    """Parse a date range from text."""
    # Common patterns: "Jan 2020 - Present", "2019-2022", etc.
    result = {
        "start_date": None,
        "end_date": None,
        "is_current": False
    }
    
    if "present" in text.lower() or "current" in text.lower():
        result["is_current"] = True
    
    # Extract years
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    if years:
        result["start_date"] = int(years[0])
        if len(years) > 1:
            result["end_date"] = int(years[-1])
        elif result["is_current"]:
            result["end_date"] = datetime.now().year
    
    return result


def calculate_duration_years(start_year: int, end_year: Optional[int] = None) -> float:
    """Calculate duration in years."""
    if end_year is None:
        end_year = datetime.now().year
    return max(0, end_year - start_year)


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix


def sanitize_for_json(obj: Any) -> Any:
    """Sanitize an object for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


def merge_skill_lists(*skill_lists: List[str]) -> List[str]:
    """Merge multiple skill lists, removing duplicates."""
    seen = set()
    result = []
    
    for skills in skill_lists:
        for skill in skills:
            skill_lower = skill.lower().strip()
            if skill_lower not in seen:
                seen.add(skill_lower)
                result.append(skill.strip())
    
    return result


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split items into batches."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed."""
        now = datetime.now()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [
            t for t in self.requests[key]
            if (now - t).total_seconds() < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add new request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        now = datetime.now()
        
        if key not in self.requests:
            return self.max_requests
        
        # Remove old requests
        self.requests[key] = [
            t for t in self.requests[key]
            if (now - t).total_seconds() < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[key]))