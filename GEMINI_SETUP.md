# Gemini API AI-Powered Skill Matching Setup

## Overview

The system now uses **AI-powered skill matching by default** powered by Google Gemini API.

### How It Works

1. **Job Title Matching** (Strict requirement): Users search by job title and location - only exact title matches are returned
2. **Skill Matching** (AI-powered): Gemini API intelligently analyzes resume vs job description to match skills semantically

This hybrid approach maintains strict job title filtering while enabling intelligent skill understanding.

## Setup Instructions

### 1. Get Gemini API Key

1. Visit https://ai.google.dev/
2. Click "Get API key" (free tier available - 60 req/min, 1500 req/day)
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

Run the app:

```bash
python run.py
```

### 3. Production Setup (Render)

1. Go to your Render service settings
2. Click "Environment" or "Env vars"
3. Add new variable:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Your Gemini API key
4. Save and redeploy

Your updates will be deployed automatically.

## How the AI Matcher Works

The AI matcher uses semantic understanding to:

- ✅ Match related but differently-worded skills (e.g., "go-to-market" matches "product launch")
- ✅ Understand context (e.g., "Product Manager" experience includes product marketing skills)
- ✅ Handle role-specific terminology (useful for Product Marketing, GTM, etc.)
- ✅ Provide confidence scores based on match quality

### Example

**Resume says:** "Managed product launch campaigns and GTM strategy"  
**Job requires:** "Product marketing and go-to-market strategy"  
**Result:** ✅ Matched (semantic understanding)

**Legacy keyword matching would:** ❌ Miss this match because exact phrases don't align

## API Usage

The API now automatically uses AI matching:

```javascript
fetch('/api/analyze', {
    method: 'POST',
    body: formData  // No need to specify useAI anymore
});
```

### Response Format

```json
{
    "jobs": [
        {
            "job": { "title": "...", "description": "..." },
            "fit_score": 75,
            "matched_strengths": ["skill1", "skill2"],
            "missing_skills": ["skill3"],
            "explanation": "Good match for product marketing background",
            "ai_powered": true
        }
    ],
    "skill_gap_summary": [...]
}
```

## API Pricing

**Google Gemini API (Free Tier)**:
- 60 requests per minute
- 1500 requests per day
- **Completely free**

Even if you exceed the free tier:
- Ultra-cheap: $0.075 per 1M tokens
- For comparison: GPT-4 is 15x more expensive

## Troubleshooting

### No GEMINI_API_KEY set

If the environment variable is missing, the system will throw an error. Make sure to:
1. Set it in `.env` (local) or Render (production)
2. Restart the app after adding the key

### Incorrect scores

AI matching should be much more generous than keyword matching. If you're still getting 0 scores:
1. Check that resume and job description are being parsed correctly
2. Verify GEMINI_API_KEY is correctly set
3. Check console logs for specific errors

## Migration from Keyword Matching

The system previously used strict keyword matching, which had limitations:
- Tier 1/2 classification was rigid
- Exact phrase matching missed related concepts
- Product Marketing roles had especially low match rates

**The new AI-powered approach is more accurate for:**
- Marketing and product roles
- GTM and launch strategies
- Roles with varied terminology
- Skills with multiple names

## Files Modified

- `app/services/ai_matcher.py` - Improved AI prompt for semantic matching
- `app/services/skill_engine.py` - Kept for backward compatibility
- `app/routes.py` - Now defaults to AI matching
- `requirements.txt` - google-generativeai, python-dotenv
- `.env.example` - GEMINI_API_KEY config
- `render.yaml` - Environment variable declaration

