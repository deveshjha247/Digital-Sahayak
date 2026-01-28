# Digital Sahayak - Product Requirements Document

## Original Problem Statement
Digital Sahayak - India's First AI-Assisted "One-Click" Job & Yojana Apply Ecosystem. An automated system for government job alerts, yojana (scheme) applications with WhatsApp integration, Cashfree payment (₹20 service fee), and document management.

## User Personas
1. **Rural/Semi-urban Youth (18-40)**: Seeking government jobs, limited digital literacy
2. **Low-income Families**: Looking for government welfare schemes
3. **CSC Operators/Cyber Cafe Owners**: Processing bulk applications
4. **Admin/Operators**: Managing job/yojana listings and applications

## Core Requirements (Static)
- Job alerts from government sources
- Yojana (scheme) listings
- WhatsApp-based alerts and application assistance
- Payment collection (₹20 service fee + govt fees)
- Document storage (DigiLocker style)
- Hindi + English language support
- Mobile-first responsive design

---

## What's Been Implemented (December 2025)

### Phase 1: MVP (Completed)
- ✅ User authentication (JWT-based)
- ✅ Job alerts CRUD with categories (Railway, SSC, UPSC, Bank, Police, etc.)
- ✅ Yojana CRUD with categories (Welfare, Education, Agriculture, Housing, etc.)
- ✅ Application management system
- ✅ Cashfree payment integration (Production mode)
- ✅ WhatsApp webhook endpoints (MOCK mode)
- ✅ Admin dashboard with stats
- ✅ Document upload endpoints
- ✅ Landing page, Job/Yojana pages with filters
- ✅ User dashboard with applications

### Phase 2: AI & Scraper (Completed - December 2025)
- ✅ **Web Scraper** for sarkariresult.com and fastjobsearchers.com
  - Background task processing
  - Auto-categorization of jobs
  - State detection
  - Duplicate prevention
- ✅ **AI Job Matching** with OpenAI
  - Education level matching (10th, 12th, Graduate, PG)
  - Age-appropriate job filtering
  - State-based job recommendations
  - Category preferences
  - Match score calculation (0-100%)
  - AI-generated reasons in Hindi
- ✅ **Profile Preferences Page** (/profile)
  - Education level selector
  - State selector
  - Age input
  - Category preferences with checkboxes
- ✅ **AI Recommendations Page** (/recommendations)
  - Match score badges
  - AI-generated match reasons
  - User profile summary
  - Refresh functionality

### Phase 3: Custom URLs & Content Management (Completed - December 2025)
- ✅ **SEO-Friendly Custom URLs**
  - Slug generation from title (e.g., /br/bpsc-70th-combined-exam-2025)
  - State prefix support (br/, jh/, up/, etc.)
  - Unique slug enforcement
  - Both ID and slug access for jobs/yojana
- ✅ **Content Draft Queue System**
  - Scraped content saved to draft queue for review
  - Admin can edit content before publishing
  - AI Rewrite feature for copyright-safe content
  - Meta description and highlights support
  - Publish workflow from drafts to live
- ✅ **Content Drafts Page** (/admin/content-drafts)
  - View pending/published drafts
  - Edit dialog with all fields
  - AI Rewrite button
  - Publish and Delete actions
- ✅ **Enhanced Job/Yojana Models**
  - slug, meta_description, highlights fields
  - source_url for reference
  - is_rewritten flag
  - content_type (job, result, admit_card, syllabus)

### Phase 4: Self-Learning AI System (Completed - January 2026)
- ✅ **Core AI Learning Engine** (`ai_learning_system.py`)
  - Learns from external AI responses (GitHub Copilot, ChatGPT, etc.)
  - Analyzes strengths/weaknesses and generates improved responses
  - Stores all learnings in MongoDB for continuous improvement
  - Calculates improvement scores (0-100%)
- ✅ **Project Context Understanding**
  - Automatically analyzes project structure (server.py, routes, models)
  - Understands Digital Sahayak domain (jobs, schemes, Indian govt systems)
  - Reads dependencies and tech stack
  - Context-aware responses specific to the project
- ✅ **Web Search Integration**
  - Real-time web search using DuckDuckGo (no API key required)
  - Search results caching (1 hour)
  - Webpage content extraction
  - Integrated into AI responses for current information
- ✅ **Smart Response Generation**
  - Uses past learnings for better outputs
  - Project-context aware
  - Optional web search for real-time data
  - Confidence scoring based on learnings applied
- ✅ **Batch Learning & Pattern Recognition**
  - Compare multiple AI responses simultaneously
  - Identify best practices automatically
  - Project-specific insights extraction
- ✅ **Enhanced Job Matching**
  - Learns from external AI suggestions
  - Web search for job eligibility criteria
  - Improved match reasoning in Hindi
- ✅ **AI Learning API Endpoints** (8 new endpoints)
  - `/ai/learn-from-external` - Learn from any AI
  - `/ai/generate-smart` - Context-aware generation
  - `/ai/web-search` - Search the web
  - `/ai/analyze-project` - Project structure analysis
  - `/ai/project-context` - Get AI's knowledge
  - `/ai/learning-stats` - Statistics dashboard
  - `/ai/batch-compare` - Multi-AI comparison
  - `/ai/improve-job-matching` - Better recommendations
- ✅ **AI Learning UI** (/ai-learning)
  - Learn from AI tab with web search option
  - Smart generation with confidence scores
  - Web search interface
  - Learning statistics dashboard
  - Analysis visualization (strengths/weaknesses)

### Design System
- ✅ Sahayak Saffron (Primary), Ashoka Navy (Secondary), Kisan Green (Accent)
- ✅ Outfit + Noto Sans fonts with Hindi support
- ✅ Ticket-style job cards
- ✅ WhatsApp green integration

### Integrations
- ✅ Cashfree Payment Gateway (PRODUCTION)
- ✅ WhatsApp Cloud API (MOCK - ready for real integration)
- ✅ OpenAI GPT API (for AI matching and self-learning)
- ✅ DuckDuckGo Web Search (for real-time information)

### Database Collections
- ✅ users, jobs, yojana, applications, payments
- ✅ content_drafts (for scraper queue)
- ✅ ai_learning_history (stores all AI learnings)
- ✅ ai_improvements (batch learning patterns)
- ✅ ai_project_context (project structure analysis)
- ✅ ai_web_search_cache (cached search results)

---

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] WhatsApp Cloud API real integration with user's Meta credentials
- [ ] Automated scraping scheduler (cron job every 6 hours)
- [ ] OTP-based phone verification

### P1 (High Priority)
- [ ] Document verification and storage with preview
- [ ] Bulk application processing for operators
- [ ] Result/notification system
- [ ] Email notifications

### P2 (Medium Priority)
- [ ] Multi-language support (regional languages)
- [ ] Browser extension for auto-fill
- [ ] Mobile app (React Native)
- [ ] API for CSCs/Cyber Cafes

---

## Next Tasks List
1. Configure WhatsApp Cloud API with real credentials, httpx (web requests)
- **Frontend**: React 19, shadcn/ui, Tailwind CSS
- **Payment**: Cashfree (Production)
- **Messaging**: WhatsApp Cloud API (MOCK)
- **AI**: OpenAI GPT API (GPT-3.5-turbo)
- **Search**: DuckDuckGo HTML search
- **Self-Learning AI**: Custom implementation with project context awareness
- **Hosting**: Digital Ocean Droplet

## Key Features Summary
1. **Job & Yojana Management**: Complete CRUD with admin controls
2. **AI Job Matching**: Education, age, state-based recommendations
3. **Web Scraping**: Automated job scraping with draft queue
4. **Content Management**: SEO-friendly URLs, meta descriptions
5. **Payment Integration**: Cashfree for service fees
6. **WhatsApp Alerts**: Notification system (MOCK ready)
7. **🆕 Self-Learning AI**: Learns from external AIs, understands project, searches web
8. **🆕 Continuous Improvement**: AI gets smarter with each interaction

## AI Learning System Capabilities
- **Multi-Source Learning**: Learns from GitHub Copilot, ChatGPT, or any AI
- **Project Intelligence**: Understands Digital Sahayak's domain and codebase
- **Web-Connected**: Can search for real-time information
- **Pattern Recognition**: Identifies best practices automatically
- **Confidence Scoring**: Tracks improvement with each learning
- **Job Matching Enhancement**: Improves recommendations over time
---

## Technical Stack
- **Backend**: FastAPI, MongoDB, Motor (async), BeautifulSoup (scraping)
- **Frontend**: React 19, shadcn/ui, Tailwind CSS
- **Payment**: Cashfree (Production)
- **Messaging**: WhatsApp Cloud API (MOCK)
- **AI**: OpenAI GPT API
- **Hosting**: Digital Ocean Droplet

## Admin Credentials
- Phone: 6200184827
- Password: admin123
