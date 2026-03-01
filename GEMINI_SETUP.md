# Gemini API AI-Powered Skill Matching Setup

This guide explains how to set up and use the Gemini AI skill matching feature.

## Overview

The system now supports two skill matching approaches:

1. **Keyword Matching** (Default): Uses predefined skill taxonomy and keyword matching - fast and free
2. **AI Matching** (Optional): Uses Google Gemini API for intelligent semantic matching - more accurate

## Setup Instructions

### 1. Get Gemini API Key

1. Visit https://ai.google.dev/
2. Click "Get API key" (free tier available)
3. Copy your API key

### 2. Local Development Setup

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Production Setup (Render)

Add the environment variable in Render Dashboard:

1. Go to your Render service settings
2. Click "Environment" or "Env vars"
3. Add new variable:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Your Gemini API key (paste your secret key)
4. Save and redeploy

## Usage

### Frontend Integration

Add a checkbox or toggle button in your UI to enable AI matching:

```html
<input type="checkbox" id="useAI" name="useAI"> Use AI for better matching
```

### API Request

Send `useAI=true` parameter in the form data:

```javascript
const formData = new FormData();
formData.append('role', 'Software Engineer');
formData.append('location', 'San Francisco');
formData.append('resume', resumeFile);
formData.append('useAI', 'true');  // Enable AI matching

fetch('/api/analyze', {
    method: 'POST',
    body: formData
});
```

### Backend Function

Use `score_fit_with_ai()` function:

```python
from app.services.skill_engine import score_fit_with_ai

# AI-powered matching
result = score_fit_with_ai(
    resume_text="Your resume text...",
    job_description="Job description text...",
    use_ai=True
)

# Falls back to keyword matching if AI fails
```

Or use hybrid matching:

```python
from app.services.skill_engine import score_fit_hybrid

result = score_fit_hybrid(
    resume_text="...",
    job_description="...",
    use_ai=True  # Combines keyword + AI
)
```

## API Pricing

**Google Gemini API (Free Tier)**:
- 60 requests per minute
- 1500 requests per day
- Completely free

This is more than enough for development and testing.

## Troubleshooting

### Missing API Key

If `GEMINI_API_KEY` is not set, the system will automatically fall back to keyword matching without errors.

### AI Request Failed

The system has built-in fallback:
- If Gemini API fails → Uses keyword matching
- Console will show error message for debugging

### Response Parsing Error

The AI matcher validates JSON responses and handles malformed responses gracefully.

## Cost Estimation

- **Free tier**: Sufficient for up to 1500 analysis requests per day
- **If exceeding limits**: $0.075 per 1M tokens (very cheap compared to GPT-4)

## Files Modified

- `requirements.txt` - Added google-generativeai, python-dotenv
- `app/services/ai_matcher.py` - New AI matching service
- `app/services/skill_engine.py` - Added AI functions
- `app/routes.py` - Updated API to support AI matching
- `.env.example` - Added GEMINI_API_KEY
- `render.yaml` - Added GEMINI_API_KEY environment variable
