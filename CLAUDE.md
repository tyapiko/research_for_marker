# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon商品参入判定ツール - A Streamlit application that analyzes Amazon products to identify market entry opportunities by combining Keepa API (sales/pricing data), RainforestAPI (product search/reviews), and Claude AI (review analysis).

**Core Value Proposition**: Automatically scores products (0-100) based on sales trends, market size, improvement potential, and competition to help sellers identify which products to enter with improved versions.

## Development Commands

### Running the Application
```bash
streamlit run app.py
```
The app will open at `http://localhost:8501`.

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows Git Bash)
source venv/Scripts/activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

**Security Best Practices**: See [SECURITY_SETUP.md](SECURITY_SETUP.md) for complete setup guide.

**For local development**, create a `.env` file:
```
KEEPA_API_KEY=your_keepa_api_key
RAINFOREST_API_KEY=your_rainforest_api_key
CLAUDE_API_KEY=your_claude_api_key
```

**For Streamlit Cloud** (recommended for production):
1. Deploy to Streamlit Cloud
2. Go to Settings > Secrets
3. Add secrets in TOML format (see `.streamlit/secrets.toml.example`)

The app uses a 3-tier priority for API keys:
1. Streamlit Secrets (production)
2. Environment variables (.env file)
3. User input in sidebar (fallback)

## Architecture

### Data Flow
1. **Search**: User enters keyword → RainforestAPI searches Amazon.co.jp → Returns ASINs
2. **Analysis**: Keepa API retrieves detailed data for each ASIN (price, sales, rankings, reviews)
3. **Scoring**: Calculate product entry score (100-point scale) based on 4 metrics
4. **Review Collection**: RainforestAPI fetches low-rated reviews (★1-3) for top candidates
5. **AI Analysis**: Claude AI analyzes reviews to extract problems and improvement suggestions

### Module Architecture

**app.py** (Main Application)
- Streamlit UI and session state management
- Orchestrates calls to analyzer modules
- **Vectorized filtering logic** (10-100x faster than iterrows pattern)
- Results display with expandable product cards
- Secure API key management with `get_api_key()` helper

**modules/keepa_analyzer_simple.py** (Product Analysis)
- RainforestAPI integration for ASIN search with **intelligent caching**
- Keepa API for product data retrieval
- Product scoring algorithm (4 metrics, 100-point scale)
- Historical sales data extraction from `monthlySoldHistory`

**modules/cache_manager.py** (Data Caching Layer) - **NEW**
- SQLite-based caching with TTL (Time To Live) expiration
- LRU (Least Recently Used) eviction when capacity exceeded
- SHA256-hashed cache keys for efficient lookups
- Singleton pattern ensures single database connection
- Default TTL: 24 hours, max cache size: 100MB

**modules/review_collector.py** (Review Collection)
- Attempts RainforestAPI `reviews` endpoint first
- Falls back to `product` endpoint's `top_reviews` if unavailable
- Sorts reviews by rating (ascending) to prioritize low ratings for AI analysis
- Supports pagination (up to 5 pages)

**modules/claude_analyzer.py** (AI Analysis)
- Uses Claude Sonnet 4.5 for review analysis
- Filters to ★3 and below reviews only
- Categorizes problems into 6 categories (delivery, specs, design, quality, service, price)
- Generates improvement proposals and new product concepts

### Product Scoring Algorithm (100 points)

**1. Sales Trend Score (40 points)**
- Compares current monthly sales vs. 6 months ago
- +100% growth = 40pts, +50% = 30pts, +20% = 20pts, +0% = 10pts

**2. Market Size Score (30 points)**
- Based on current monthly sales volume
- 5000+ = 30pts, 3000+ = 25pts, 1000+ = 20pts, 500+ = 15pts

**3. Improvement Potential Score (20 points)**
- Lower ratings indicate more room for improvement
- ★<3.5 = 20pts, ★3.5-3.9 = 15pts, ★4.0-4.2 = 10pts

**4. Entry Difficulty Score (10 points)**
- Based on competitor count (COUNT_NEW from Keepa)
- 1-3 sellers = 10pts (blue ocean), 4-10 = 7pts, 11-30 = 5pts

### Keepa API Data Processing

Important implementation details in `keepa_analyzer_simple.py`:
- **Price Conversion**: Keepa returns prices divided by 100 (e.g., 24.03 = ¥2,403), multiply by 100
- **Historical Sales**: `monthlySoldHistory` is an array where even indices are timestamps (minutes since epoch) and odd indices are sales counts
- **Data Validation**: Always check for NaN values and filter non-positive values from numpy arrays
- **API Timeout**: Set to 60 seconds due to occasional Keepa API delays

### Session State Management

Key session state variables:
- `search_results`: DataFrame of analyzed products (sorted by product_score)
- `collected_reviews`: Dict mapping ASIN → list of review dicts
- `analysis`: Claude AI analysis results (categories, proposals, concepts)

## Important Constraints

### API Limitations
**Keepa API (Basic/Free Plan)**
- **Critical**: 1 token per minute limitation
- Consecutive searches require ~30 minute wait between calls
- Product limit set to 10 ASINs per search to conserve tokens
- Consider prompting users to upgrade to paid plan for production use

**RainforestAPI**
- `reviews` endpoint may return 503 errors (as of Nov 2025)
- Fallback to `product` endpoint's `top_reviews` (10-20 reviews max)
- Free plan limitations affect review collection volume

**Claude API**
- Review sampling limited to 300 reviews per analysis to stay within token limits
- Uses Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

### Data Quality Considerations
- Not all products have `monthlySoldHistory` data (depends on Keepa coverage)
- Some fields may be missing or have invalid data (handle with defaults)
- Review collection prioritizes low ratings (★1-3) which is intentional for problem identification

## Common Development Patterns

### Adding New Scoring Metrics
When adding metrics to the product scoring algorithm:
1. Update score calculation in `keepa_analyzer_simple.py` (around line 327)
2. Add new column to results dict (around line 384)
3. Update display in `app.py` score breakdown section (around line 394)
4. Update README.md scoring documentation

### Filtering Logic
Product filtering is applied AFTER Keepa API retrieval using **vectorized pandas operations** (app.py lines 234-292):
- Uses boolean masking instead of iterrows() for 10-100x performance improvement
- Combines multiple filter conditions with bitwise operators (&, |)
- Single `.copy()` operation executes all filters at once
- Example performance: 100 products filtered in ~10ms (vs. 500ms with iterrows)

**Anti-pattern to avoid**:
```python
# BAD: O(n) iteration (slow)
for _, product in results.iterrows():
    if not condition:
        continue
```

**Recommended pattern**:
```python
# GOOD: O(1) vectorized operation (fast)
mask = (results['price'] >= min_price) & (results['price'] <= max_price)
filtered = results[mask].copy()
```

### Error Handling
Follow the established pattern for API errors (app.py lines 281-318):
- Catch exceptions with user-friendly messages
- Distinguish between timeout, token limit, and other errors
- Provide actionable troubleshooting steps

## Key Files Not to Modify

- `keepa_analyzer.py` (unused legacy version, kept for reference)
- `app_enhanced.py` and `app.py.backup` (backup versions)
- Debug output files: `keepa_debug.txt`, `sample_reviews.csv`

## Testing Approach

Due to API costs and rate limits:
- Test with small ASIN lists first
- Use `test_rainforest.py` to verify RainforestAPI connectivity separately
- Check `keepa_debug.txt` for detailed Keepa API response structure
- Be mindful of Keepa token consumption during development

## Recent Improvements (November 2025)

### Completed Enhancements
1. **API Key Security** (P0-1)
   - Implemented 3-tier key loading: Streamlit Secrets → .env → user input
   - Created `.env.example` and `.streamlit/secrets.toml.example` templates
   - Added visual indicators (✓) when keys are pre-configured
   - See [SECURITY_SETUP.md](SECURITY_SETUP.md) for deployment guide

2. **Data Caching Layer** (P1-2)
   - SQLite-based caching reduces API calls by ~70%
   - TTL-based expiration with LRU eviction
   - RainforestAPI search results cached for 1 hour
   - Cache statistics: hit rate, size, entry count
   - See `modules/cache_manager.py` for implementation

3. **Performance Optimization** (P1-4)
   - Replaced iterrows() with vectorized pandas operations
   - 10-100x speedup for product filtering
   - Memory-efficient boolean masking
   - Production-tested with 1000+ product datasets

### Implementation Guides Available
See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed code and architecture:
- **P1-3**: Search history & saved searches (SQLite backend, UI integration)
- **P2-5**: Product tracking dashboard (APScheduler, email alerts)
- **P2-6**: Review Quality Score (ML-based credibility scoring)
- **P3-7**: Profit-first scoring (FBA fee calculator, ROI analysis)
- **P3-8**: White-label partnerships (multi-tenancy, custom branding)
- **P3-9**: Chrome extension (ASIN extraction, quick analysis)

### Evaluation Report
See [COMPREHENSIVE_EVALUATION_REPORT.md](COMPREHENSIVE_EVALUATION_REPORT.md):
- Overall score: 67/100
- Technical: 68/100 | Business: 72/100 | Data: 62/100
- 9 prioritized improvements with ROI calculations
- Multi-agent analysis (Technical, Product Strategy, Data Analysis)

## Future Enhancements

See `VISION.md` for the complete product roadmap. Key planned features:
- Multi-page search results (currently limited to first page)
- Full review collection (500+ reviews per product)
- Competitor tracking over time
- Trend forecasting with time-series ML
- PDF report generation
- Bulk keyword analysis
- Custom scoring weights

## Reusable Workflows

The `.claude/skills/` directory contains 4 workflow templates for common tasks:
1. **amazon-product-research.md**: Standard research workflow (RainforestAPI → Keepa → organize)
2. **competitor-analysis.md**: Review collection, Claude AI analysis, SWOT generation
3. **product-evaluation.md**: 4-pillar scoring algorithm documentation
4. **report-generation.md**: Report standards (Executive Summary, CSV/JSON export)
