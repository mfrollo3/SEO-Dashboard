"""
TruPath SEO Command Center
==========================
One dashboard to rule them all.

Deploy: streamlit run app.py
Or deploy to Streamlit Cloud for free.
"""

import streamlit as st
import os
import json
import time
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

# Page config
st.set_page_config(
    page_title="SEO Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = None
if 'generated_pages' not in st.session_state:
    st.session_state.generated_pages = []
if 'current_site' not in st.session_state:
    st.session_state.current_site = None

# =============================================================================
# SITE CONFIGURATIONS - Add new sites here
# =============================================================================

SITES = {
    "trupathnj": {
        "name": "TruPath Recovery NJ",
        "domain": "trupathnj.com",
        "parent_org": "Quantum Behavioral",
        "phone": "(732) 281-6005",
        "address": "1129 Hooper Avenue, Suite 2, Toms River, NJ 08753",
        "services": ["Inpatient Treatment", "Outpatient Programs", "Medical Detox", "Dual Diagnosis"],
        "niche": "addiction_treatment",
        "target_locations": [
            "Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Elizabeth, NJ",
            "Toms River, NJ", "Trenton, NJ", "Camden, NJ", "Edison, NJ",
            "Woodbridge, NJ", "Lakewood, NJ", "Hoboken, NJ", "Brick, NJ",
            "Cherry Hill, NJ", "Atlantic City, NJ", "Hackensack, NJ",
            "Manhattan, NY", "Brooklyn, NY", "Philadelphia, PA"
        ],
        "seed_keywords": [
            "drug rehab", "inpatient drug rehab", "alcohol rehab", "inpatient alcohol rehab",
            "detox centers", "medical detox", "addiction treatment", "heroin rehab",
            "opioid treatment", "dual diagnosis treatment", "cocaine rehab",
            "residential treatment", "outpatient drug rehab", "MAT treatment"
        ],
        "insurance_focus": "PPO only - no Medicaid/Medicare",
        "wp_url": "",
        "wp_user": "",
        "wp_password": ""
    },
    "trupath_la": {
        "name": "TruPath Recovery LA",
        "domain": "trupathla.com",
        "parent_org": "TruPath LA Facility",
        "phone": "(555) 000-0000",
        "address": "Los Angeles, CA",
        "services": ["Inpatient Treatment", "Outpatient Programs", "Medical Detox"],
        "niche": "addiction_treatment",
        "target_locations": [
            "Los Angeles, CA", "Beverly Hills, CA", "Santa Monica, CA",
            "Malibu, CA", "Pasadena, CA", "Long Beach, CA", "Burbank, CA"
        ],
        "seed_keywords": [
            "drug rehab", "inpatient drug rehab", "alcohol rehab", "luxury rehab",
            "detox centers", "addiction treatment", "heroin rehab", "cocaine rehab"
        ],
        "insurance_focus": "PPO only - no Medicaid/Medicare",
        "wp_url": "",
        "wp_user": "",
        "wp_password": ""
    },
    # ADD MORE SITES HERE - just copy the template above
}

NICHE_TEMPLATES = {
    "addiction_treatment": {
        "paa_templates": [
            "How much does {keyword} cost?",
            "Does insurance cover {keyword}?",
            "How long is {keyword}?",
            "What is the success rate of {keyword}?",
            "What happens during {keyword}?"
        ],
        "content_requirements": {
            "insurance": "PPO only, never mention Medicaid/Medicare",
            "tone": "Helpful directory, not facility marketing",
            "cta": "Free consultation, no pressure"
        }
    },
    "home_services": {
        "paa_templates": [
            "How much does {keyword} cost?",
            "How long does {keyword} take?",
            "Is {keyword} worth it?",
            "What should I look for in {keyword}?",
            "When is the best time for {keyword}?"
        ],
        "content_requirements": {
            "tone": "Local expert, trustworthy",
            "cta": "Free estimate"
        }
    },
    "health_insurance": {
        "paa_templates": [
            "How much does {keyword} cost?",
            "What does {keyword} cover?",
            "How do I qualify for {keyword}?",
            "When can I enroll in {keyword}?",
            "What's the difference between {keyword} plans?"
        ],
        "content_requirements": {
            "compliance": "No specific health claims",
            "tone": "Helpful broker, educational"
        }
    }
}

# =============================================================================
# SERP EXTRACTION
# =============================================================================

class SERPExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.results = {
            'pages_to_build': [],
            'total_keywords': 0,
            'extraction_date': datetime.now().isoformat()
        }
    
    def get_autocomplete(self, query: str) -> List[str]:
        """Get Google autocomplete suggestions"""
        suggestions = []
        try:
            url = "http://suggestqueries.google.com/complete/search"
            params = {"client": "firefox", "q": query}
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if len(data) > 1:
                suggestions = data[1]
        except:
            pass
        return suggestions
    
    def get_serp_data(self, keyword: str, location: str) -> Dict:
        """Get PAA and related searches from SerpAPI"""
        if not self.api_key:
            return {'paa': [], 'related': []}
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": f"{keyword} {location}",
                "location": f"{location.split(',')[0]}, United States",
                "api_key": self.api_key,
                "engine": "google"
            }
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            paa = [q.get('question', '') for q in data.get('related_questions', [])]
            related = [r.get('query', '') for r in data.get('related_searches', [])]
            
            return {'paa': paa, 'related': related}
        except Exception as e:
            return {'paa': [], 'related': [], 'error': str(e)}
    
    def calculate_priority(self, keyword: str, location: str, paa_count: int, related_count: int) -> int:
        """Score 0-100 based on opportunity signals"""
        score = 50
        
        # More PAA = more opportunity
        score += min(paa_count * 5, 25)
        
        # More related searches = broader topic
        score += min(related_count * 2, 15)
        
        # Major cities boost
        major = ['Newark', 'Jersey City', 'Manhattan', 'Brooklyn', 'Philadelphia', 
                 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
        if any(city in location for city in major):
            score += 10
        
        # High-intent keywords boost
        high_intent = ['inpatient', 'cost', 'insurance', 'near me', 'best', 'detox']
        if any(term in keyword.lower() for term in high_intent):
            score += 10
        
        return min(score, 100)
    
    def extract_all(self, keywords: List[str], locations: List[str], progress_callback=None) -> Dict:
        """Full extraction for all keyword/location combinations"""
        total = len(keywords) * len(locations)
        current = 0
        
        for location in locations:
            for keyword in keywords:
                current += 1
                full_keyword = f"{keyword} {location.split(',')[0]}"
                
                if progress_callback:
                    progress_callback(current / total, f"Processing: {full_keyword}")
                
                # Get SERP data
                serp = self.get_serp_data(keyword, location)
                
                # Calculate priority
                priority = self.calculate_priority(
                    keyword, location, 
                    len(serp.get('paa', [])), 
                    len(serp.get('related', []))
                )
                
                # Add to results
                self.results['pages_to_build'].append({
                    'full_keyword': full_keyword,
                    'keyword': keyword,
                    'location': location,
                    'paa_questions': serp.get('paa', []),
                    'related_searches': serp.get('related', []),
                    'priority': priority
                })
                
                # Rate limiting for SerpAPI
                if self.api_key:
                    time.sleep(2)
        
        # Sort by priority
        self.results['pages_to_build'].sort(key=lambda x: x['priority'], reverse=True)
        self.results['total_keywords'] = len(self.results['pages_to_build'])
        
        # Tier the results
        pages = self.results['pages_to_build']
        self.results['tier_1'] = [p for p in pages if p['priority'] >= 80]
        self.results['tier_2'] = [p for p in pages if 65 <= p['priority'] < 80]
        self.results['tier_3'] = [p for p in pages if 50 <= p['priority'] < 65]
        self.results['tier_4'] = [p for p in pages if p['priority'] < 50]
        
        return self.results

# =============================================================================
# CONTENT GENERATION
# =============================================================================

class ContentGenerator:
    def __init__(self, api_key: str, site_config: Dict):
        self.api_key = api_key
        self.site = site_config
        
    def generate_page(self, keyword: str, location: str, paa_questions: List[str]) -> Dict:
        """Generate page content using Claude"""
        
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key)
        
        paa_str = "\n".join([f"- {q}" for q in paa_questions[:5]]) if paa_questions else "- How much does treatment cost?\n- Does insurance cover this?"
        
        prompt = f"""Generate a treatment resource page. Output ONLY valid JSON.

SITE: {self.site['name']} ({self.site['domain']})
PARENT ORG: {self.site['parent_org']}
PHONE: {self.site['phone']}
ADDRESS: {self.site['address']}

KEYWORD: {keyword}
LOCATION: {location}

PAA QUESTIONS:
{paa_str}

REQUIREMENTS:
- {self.site.get('insurance_focus', 'Accept most insurance')}
- Helpful directory voice, NOT facility marketing
- Mention {self.site['parent_org']} naturally as serving the area

Generate this JSON:

{{
  "title": "{keyword.title()} | {self.site['name']}",
  "meta_description": "Find {keyword} options in {location}. Free guidance on costs, insurance, and programs. Call 24/7.",
  "slug": "{keyword.lower().replace(' ', '-')}-{location.lower().split(',')[0].replace(' ', '-')}",
  "h1": "{keyword.title()}",
  "subtitle": "Expert Guidance for {location} Area Residents",
  "sections": [
    {{"heading": "Understanding {keyword.title()}", "content": "[150-200 words educational overview]"}},
    {{"heading": "Options Near {location}", "content": "[150-200 words on local treatment landscape, mention {self.site['parent_org']}]"}},
    {{"heading": "Cost and Insurance", "content": "[150-200 words on costs and PPO coverage - NO Medicaid/Medicare]"}},
    {{"heading": "What to Expect", "content": "[150-200 words on treatment process]"}}
  ],
  "faqs": [
    {{"q": "[PAA question 1]", "a": "[50-75 word answer]"}},
    {{"q": "[PAA question 2]", "a": "[50-75 word answer]"}},
    {{"q": "[PAA question 3]", "a": "[50-75 word answer]"}}
  ]
}}

Output ONLY valid JSON."""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = message.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            return json.loads(text.strip())
        except Exception as e:
            return {"error": str(e)}
    
    def to_wordpress_html(self, content: Dict) -> str:
        """Convert to WordPress-ready HTML"""
        
        html = f'''<div class="tp-hero">
  <h1>{content.get('h1', '')}</h1>
  <p>{content.get('subtitle', '')}</p>
  <a href="tel:{self.site['phone'].replace('(','').replace(')','').replace('-','').replace(' ','')}" class="btn-green">Call Now</a>
  <a href="#form" class="btn-white">Get Free Info</a>
</div>

<div class="tp-content">
'''
        for section in content.get('sections', []):
            html += f"<h2>{section.get('heading', '')}</h2>\n"
            html += f"<p>{section.get('content', '')}</p>\n\n"
        
        if content.get('faqs'):
            html += "<h2>Frequently Asked Questions</h2>\n"
            for faq in content['faqs']:
                html += f"<p><strong>{faq.get('q', '')}</strong></p>\n"
                html += f"<p>{faq.get('a', '')}</p>\n"
        
        html += f'''
<div id="form" class="tp-form">
  <h2>Get Free Information</h2>
  <form action="YOUR_FORM_ENDPOINT" method="POST">
    <input type="text" name="name" placeholder="Name" required>
    <input type="tel" name="phone" placeholder="Phone" required>
    <button type="submit">Request Callback</button>
  </form>
</div>
</div>

<div class="tp-cta">
  <h2>Ready to Take the Next Step?</h2>
  <p>Free, confidential guidance 24/7</p>
  <a href="tel:{self.site['phone'].replace('(','').replace(')','').replace('-','').replace(' ','')}">Call: {self.site['phone']}</a>
</div>'''
        
        return html

# =============================================================================
# WORDPRESS PUBLISHING
# =============================================================================

class WordPressPublisher:
    def __init__(self, url: str, user: str, password: str):
        self.url = url.rstrip('/')
        self.auth = (user, password)
    
    def publish_page(self, title: str, content: str, slug: str, meta_desc: str, publish_date: str = None) -> Dict:
        """Publish page to WordPress"""
        
        endpoint = f"{self.url}/wp-json/wp/v2/pages"
        
        data = {
            'title': title,
            'content': content,
            'slug': slug,
            'status': 'publish',
            'meta': {'description': meta_desc}
        }
        
        if publish_date:
            data['date'] = publish_date
        
        try:
            response = requests.post(endpoint, json=data, auth=self.auth, timeout=30)
            response.raise_for_status()
            result = response.json()
            return {'success': True, 'id': result.get('id'), 'url': result.get('link')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# =============================================================================
# STREAMLIT UI
# =============================================================================

def main():
    st.title("🚀 SEO Command Center")
    st.markdown("*One dashboard. Unlimited locations. Total domination.*")
    
    # Sidebar - Site Selection & API Keys
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Site selector
        site_key = st.selectbox(
            "Select Site",
            options=list(SITES.keys()),
            format_func=lambda x: SITES[x]['name']
        )
        site = SITES[site_key]
        st.session_state.current_site = site
        
        st.divider()
        
        # API Keys
        st.subheader("API Keys")
        serpapi_key = st.text_input("SerpAPI Key", type="password", key="serpapi")
        anthropic_key = st.text_input("Anthropic Key", type="password", key="anthropic")
        
        st.divider()
        
        # WordPress Config
        st.subheader("WordPress")
        wp_url = st.text_input("WP URL", value=site.get('wp_url', ''), placeholder="https://yoursite.com")
        wp_user = st.text_input("WP User", value=site.get('wp_user', ''))
        wp_pass = st.text_input("WP App Password", type="password")
        
        st.divider()
        
        # Site info
        st.subheader("Current Site")
        st.write(f"**{site['name']}**")
        st.write(f"Domain: {site['domain']}")
        st.write(f"Locations: {len(site['target_locations'])}")
        st.write(f"Keywords: {len(site['seed_keywords'])}")
    
    # Main content - Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Extract", "✍️ Generate", "📤 Publish", "📈 Status"])
    
    # ===================
    # TAB 1: EXTRACTION
    # ===================
    with tab1:
        st.header("SERP Data Extraction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Keywords")
            keywords = st.multiselect(
                "Select keywords to extract",
                options=site['seed_keywords'],
                default=site['seed_keywords'][:5]
            )
            custom_keywords = st.text_area("Add custom keywords (one per line)")
            if custom_keywords:
                keywords.extend([k.strip() for k in custom_keywords.split('\n') if k.strip()])
        
        with col2:
            st.subheader("Locations")
            locations = st.multiselect(
                "Select locations",
                options=site['target_locations'],
                default=site['target_locations'][:5]
            )
            custom_locations = st.text_area("Add custom locations (one per line)")
            if custom_locations:
                locations.extend([l.strip() for l in custom_locations.split('\n') if l.strip()])
        
        total_combinations = len(keywords) * len(locations)
        estimated_time = total_combinations * 2.5 / 60  # ~2.5 seconds per with rate limiting
        
        st.info(f"**{total_combinations}** keyword/location combinations | Estimated time: **{estimated_time:.1f} minutes**")
        
        if st.button("🔍 Start Extraction", type="primary", use_container_width=True):
            if not serpapi_key:
                st.error("SerpAPI key required")
            else:
                extractor = SERPExtractor(serpapi_key)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(pct, msg):
                    progress_bar.progress(pct)
                    status_text.text(msg)
                
                with st.spinner("Extracting SERP data..."):
                    results = extractor.extract_all(keywords, locations, update_progress)
                
                st.session_state.extraction_results = results
                
                st.success(f"✅ Extraction complete! Found **{results['total_keywords']}** pages to build.")
                
                # Show tier breakdown
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Tier 1 (80+)", len(results.get('tier_1', [])))
                col2.metric("Tier 2 (65-79)", len(results.get('tier_2', [])))
                col3.metric("Tier 3 (50-64)", len(results.get('tier_3', [])))
                col4.metric("Tier 4 (<50)", len(results.get('tier_4', [])))
        
        # Show results if available
        if st.session_state.extraction_results:
            st.divider()
            st.subheader("Extraction Results")
            
            df = pd.DataFrame(st.session_state.extraction_results['pages_to_build'])
            df = df[['priority', 'full_keyword', 'location', 'paa_questions']]
            df['paa_count'] = df['paa_questions'].apply(len)
            
            st.dataframe(df.drop('paa_questions', axis=1), use_container_width=True)
            
            # Download button
            json_str = json.dumps(st.session_state.extraction_results, indent=2)
            st.download_button(
                "📥 Download Build Plan (JSON)",
                json_str,
                file_name=f"build_plan_{site_key}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    # ===================
    # TAB 2: GENERATION
    # ===================
    with tab2:
        st.header("Content Generation")
        
        if not st.session_state.extraction_results:
            st.warning("Run extraction first, or upload a build plan.")
            
            uploaded = st.file_uploader("Upload build plan JSON", type="json")
            if uploaded:
                st.session_state.extraction_results = json.load(uploaded)
                st.success("Build plan loaded!")
                st.rerun()
        else:
            results = st.session_state.extraction_results
            
            # Tier selection
            tier = st.selectbox(
                "Select tier to generate",
                options=["tier_1", "tier_2", "tier_3", "tier_4"],
                format_func=lambda x: f"{x.replace('_', ' ').title()} ({len(results.get(x, []))} pages)"
            )
            
            pages_in_tier = results.get(tier, [])
            
            limit = st.slider("Number of pages to generate", 1, min(50, len(pages_in_tier)), min(5, len(pages_in_tier)))
            
            st.info(f"Will generate **{limit}** pages from {tier.replace('_', ' ').title()}")
            
            if st.button("✍️ Generate Content", type="primary", use_container_width=True):
                if not anthropic_key:
                    st.error("Anthropic API key required")
                else:
                    generator = ContentGenerator(anthropic_key, site)
                    
                    progress = st.progress(0)
                    status = st.empty()
                    
                    generated = []
                    
                    for i, page in enumerate(pages_in_tier[:limit]):
                        progress.progress((i + 1) / limit)
                        status.text(f"Generating: {page['full_keyword']}")
                        
                        content = generator.generate_page(
                            page['keyword'],
                            page['location'],
                            page.get('paa_questions', [])
                        )
                        
                        if 'error' not in content:
                            html = generator.to_wordpress_html(content)
                            
                            # Random backdate
                            days_ago = random.randint(1, 180)
                            publish_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S')
                            
                            generated.append({
                                'keyword': page['full_keyword'],
                                'content': content,
                                'html': html,
                                'publish_date': publish_date
                            })
                        
                        time.sleep(1)  # Rate limiting
                    
                    st.session_state.generated_pages.extend(generated)
                    st.success(f"✅ Generated **{len(generated)}** pages!")
            
            # Show generated pages
            if st.session_state.generated_pages:
                st.divider()
                st.subheader(f"Generated Pages ({len(st.session_state.generated_pages)})")
                
                for i, page in enumerate(st.session_state.generated_pages[-10:]):  # Show last 10
                    with st.expander(f"{page['keyword']} | {page['publish_date'][:10]}"):
                        st.code(page['html'][:500] + "...", language="html")
    
    # ===================
    # TAB 3: PUBLISHING
    # ===================
    with tab3:
        st.header("WordPress Publishing")
        
        if not st.session_state.generated_pages:
            st.warning("Generate content first.")
        else:
            st.info(f"**{len(st.session_state.generated_pages)}** pages ready to publish")
            
            if not wp_url or not wp_user or not wp_pass:
                st.error("WordPress credentials required (see sidebar)")
            else:
                publish_limit = st.slider("Pages to publish", 1, len(st.session_state.generated_pages), min(10, len(st.session_state.generated_pages)))
                
                if st.button("📤 Publish to WordPress", type="primary", use_container_width=True):
                    publisher = WordPressPublisher(wp_url, wp_user, wp_pass)
                    
                    progress = st.progress(0)
                    status = st.empty()
                    
                    success = 0
                    failed = 0
                    
                    for i, page in enumerate(st.session_state.generated_pages[:publish_limit]):
                        progress.progress((i + 1) / publish_limit)
                        status.text(f"Publishing: {page['keyword']}")
                        
                        result = publisher.publish_page(
                            title=page['content'].get('title', page['keyword']),
                            content=page['html'],
                            slug=page['content'].get('slug', ''),
                            meta_desc=page['content'].get('meta_description', ''),
                            publish_date=page['publish_date']
                        )
                        
                        if result.get('success'):
                            success += 1
                        else:
                            failed += 1
                        
                        time.sleep(0.5)
                    
                    st.success(f"✅ Published **{success}** pages | Failed: {failed}")
    
    # ===================
    # TAB 4: STATUS
    # ===================
    with tab4:
        st.header("Project Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Keywords Extracted", 
                     st.session_state.extraction_results.get('total_keywords', 0) if st.session_state.extraction_results else 0)
        
        with col2:
            st.metric("Pages Generated", len(st.session_state.generated_pages))
        
        with col3:
            st.metric("Current Site", site['name'])
        
        st.divider()
        
        # Site overview
        st.subheader("Site Configuration")
        st.json(site)
        
        # Export all data
        if st.session_state.generated_pages:
            st.divider()
            st.subheader("Export")
            
            export_data = {
                'site': site_key,
                'extraction': st.session_state.extraction_results,
                'generated_pages': st.session_state.generated_pages,
                'exported_at': datetime.now().isoformat()
            }
            
            st.download_button(
                "📥 Export All Data",
                json.dumps(export_data, indent=2),
                file_name=f"seo_export_{site_key}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
