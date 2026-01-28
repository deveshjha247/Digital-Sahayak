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

### Design System
- ✅ Sahayak Saffron (Primary), Ashoka Navy (Secondary), Kisan Green (Accent)
- ✅ Outfit + Noto Sans fonts with Hindi support
- ✅ Ticket-style job cards
- ✅ WhatsApp green integration

### Integrations
- ✅ Cashfree Payment Gateway (PRODUCTION)
- ✅ WhatsApp Cloud API (MOCK - ready for real integration)
- ✅ OpenAI GPT API (for AI matching)

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
1. Configure WhatsApp Cloud API with real credentials
2. Set up automated scraping scheduler
3. Implement OTP verification for registration
4. Add document upload with preview
5. Create operator bulk processing interface

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
