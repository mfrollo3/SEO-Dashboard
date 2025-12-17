# SEO Command Center

One dashboard to manage SEO content generation across all your sites.

## Features

- **Multi-Site Support**: Switch between TruPath NJ, LA, or any site you add
- **SERP Extraction**: Pull real PAA questions, related searches via SerpAPI
- **Content Generation**: Claude-powered content following your frameworks
- **WordPress Publishing**: Direct publish with random backdating
- **Export Everything**: Download build plans, generated content

## Quick Deploy (Streamlit Cloud - FREE)

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set secrets (API keys) in Streamlit Cloud dashboard
5. Done - access from any browser

## Local Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## Adding New Sites

Edit `app.py`, find the `SITES` dictionary, copy an existing site config:

```python
"your_new_site": {
    "name": "Your Site Name",
    "domain": "yoursite.com",
    "parent_org": "Your Organization",
    "phone": "(555) 000-0000",
    "address": "Your Address",
    "services": ["Service 1", "Service 2"],
    "niche": "addiction_treatment",  # or "home_services", "health_insurance"
    "target_locations": ["City 1", "City 2"],
    "seed_keywords": ["keyword 1", "keyword 2"],
    "insurance_focus": "Your requirements",
    "wp_url": "",
    "wp_user": "",
    "wp_password": ""
}
```

## API Keys Needed

- **SerpAPI**: For SERP data extraction - https://serpapi.com
- **Anthropic**: For content generation - https://console.anthropic.com

## The Workflow

1. **Select Site** (sidebar dropdown)
2. **Extract Tab**: Choose keywords + locations → Extract SERP data
3. **Generate Tab**: Select tier → Generate content
4. **Publish Tab**: Push to WordPress with backdated timestamps
5. **Status Tab**: Monitor progress, export data

## Fits The Plan

✅ Data-driven keyword selection (real SERP data)
✅ Quality content (Claude generation with guardrails)
✅ Proper structure (3-layer framework built in)
✅ Scalable (add unlimited sites)
✅ Random backdating (looks natural)
✅ No Medicaid/Medicare (quality checks)
