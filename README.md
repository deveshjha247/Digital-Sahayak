# Digital Sahayak - Government Schemes & Job Portal

A comprehensive platform connecting citizens with government schemes and job opportunities through intelligent matching powered by **Digital Sahayak AI** - our custom-built AI system developed from scratch.

## Features

### 🎯 Core Functionalities
- **Yojana Discovery**: Browse and search government schemes (Yojanas)
- **Job Listings**: Explore available job opportunities
- **Digital Sahayak AI**: Custom-built AI for intelligent job matching and recommendations
- **DS-Search**: Intelligent web search with policy-based query routing
- **Evidence Extractor**: Converts raw search results into structured facts
- **DS-Talk NLG**: Natural language generation with 100+ Hindi/English templates
- **Hybrid Matching Engine**: Rule-based + ML approach for accurate matching
- **Form Intelligence**: Smart form filling and error prediction
- **Self-Learning System**: Continuously improves from user interactions
- **Admin Dashboard**: Manage schemes and jobs content
- **User Authentication**: Secure login and registration
- **Profile Management**: User preferences and profile settings

### 🛠️ Tech Stack

**Frontend**
- React.js with modern component architecture
- Tailwind CSS for styling
- Shadcn UI components for consistent design
- React Router for navigation

**Backend**
- Python FastAPI server
- **Digital Sahayak AI** - Custom ML engine built from scratch
- **DS-Search v2.0** - Intelligent search with Evidence Extractor & DS-Talk NLG
- MongoDB for data persistence
- Hybrid Matching Engine (Rule-based + Heuristics + ML)
- Form Intelligence System (Field classification & error prediction)
- YAML-based Hyperparameter Configuration
- RESTful API architecture

**Tools & Libraries**
- Node.js for frontend build process
- Webpack for module bundling
- Git for version control

## Project Structure

```
Digital-Sahayak/
├── frontend/              # React.js application
│   ├── public/           # Static assets
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── context/      # Context API (Auth)
│   │   ├── hooks/        # Custom React hooks
│   │   └── lib/          # Utility functions
│   └── plugins/          # Webpack and build plugins
├── backend/              # Python FastAPI server
│   ├── server.py         # Main application
│   ├── ai_learning_system.py # Digital Sahayak AI core
│   ├── ai/               # AI Modules
│   │   ├── config/       # Hyperparameters (YAML) & model registry
│   │   ├── search/       # DS-Search (policy, crawler, ranker, cache)
│   │   ├── evidence/     # Evidence Extractor (facts engine)
│   │   ├── nlg/          # DS-Talk NLG (100+ templates)
│   │   ├── data/         # Training data (raw, processed)
│   │   └── training/     # Model training configs
│   ├── models/           # Data models & checkpoints
│   │   ├── checkpoints/  # Training checkpoints
│   │   ├── production/   # Production models
│   │   └── experiments/  # Experimental models
│   ├── notebooks/        # Jupyter notebooks for experiments
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   └── requirements.txt  # Python dependencies
├── memory/               # Documentation and PRD
└── tests/                # Test files
```

## Getting Started

### Prerequisites
- Node.js (v14+)
- Python 3.8+
- npm or yarn

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python server.py
```

## Environment Variables

Create a `.env` file in the backend directory:

```
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET_KEY=your_secret_key_here
CASHFREE_APP_ID=your_cashfree_app_id
CASHFREE_SECRET_KEY=your_cashfree_secret
```

## Pages & Routes

- **Home**: Landing page with scheme and job highlights
- **Login/Register**: User authentication
- **Yojana Page**: Browse government schemes
- **Jobs Page**: View available job listings
- **Job Details**: Detailed job information with AI matching
- **Dashboard**: User dashboard with recommendations
- **Admin Page**: Content management for schemes and jobs
- **Profile**: User profile and preferences

## Development Notes

- The project uses Context API for state management (Authentication)
- UI components are built with Shadcn and styled with Tailwind CSS
- Backend provides RESTful endpoints for data management
- **Digital Sahayak AI**: Custom-built matching engine with rule-based + ML hybrid approach
- **Self-Learning System**: Learns from user behavior (applications, interactions) to improve recommendations
- Modular architecture for scalability and maintainability

## Digital Sahayak AI System

Our custom-built **Digital Sahayak AI** is developed from scratch and includes:

### 🤖 Hybrid Matching Engine
- **Rule-based Matching**: Deterministic field mappings (education, age, state, category)
- **Heuristic Scoring**: Pattern-based matching with learned weights
- **Log-based Learning**: Learns from user behavior (applications, saves, ignores)
- **Confidence Scoring**: Provides match confidence with explanations in Hindi & English

### 📋 Form Intelligence
- **Field Classification**: Auto-detects form field types (name, email, Aadhar, PAN, etc.)
- **Error Prediction**: Validates forms before submission
- **Smart Auto-fill**: Suggests values based on user profile
- **Portal Training**: Learns from portal-specific form datasets

### � DS-Search v2.0
- **Policy Router**: Decides when to search web vs use cached knowledge
- **Query Generator**: Optimizes queries for Indian government portals
- **Smart Crawler**: Extracts content with trust scoring (.gov.in = 1.0)
- **Evidence Extractor**: Transforms raw results into structured facts
- **DS-Talk NLG**: 100+ Hindi/English templates for natural responses
- **Result Ranker**: Re-ranks results based on relevance and trust

### ⚙️ Configuration Management
- **YAML-based Hyperparameters**: Easy to modify without code changes
- **Model Registry**: Track trained models and versions
- **Jupyter Notebooks**: Experiments and training

### �📊 Continuous Learning
- Tracks user interactions (applied, ignored, saved jobs/schemes)
- Updates matching patterns based on successful applications
- Improves recommendations over time
- No dependency on external AI APIs - built completely in-house

See [REFACTORING_GUIDE.md](backend/REFACTORING_GUIDE.md) and [FORM_INTELLIGENCE_GUIDE.md](backend/FORM_INTELLIGENCE_GUIDE.md) for detailed documentation.

**📖 Complete AI Documentation:** See [DIGITAL_SAHAYAK_AI.md](DIGITAL_SAHAYAK_AI.md) for how our custom AI works without external dependencies.

## Apply AI Engine v1 🚀

**Digital Sahayak's AI is now productized as "Apply AI Engine v1"** - a standalone API that can be used for:

- **Internal Use**: Power Digital Sahayak platform
- **API Service**: Offer as SaaS to other platforms
- **White-label**: Deploy for enterprise clients

### Key Features:
- ✅ Job/Scheme matching API
- ✅ Form field classification
- ✅ Error prediction & validation
- ✅ Auto-fill suggestions
- ✅ Behavioral learning
- ✅ RESTful API with authentication
- ✅ Usage tracking & analytics

**API Documentation:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)  
**Product Details:** [APPLY_AI_ENGINE.md](APPLY_AI_ENGINE.md)

## Contributors

This project is a collaborative effort by:
- **Devesh Kumar Jha** (@deveshkumarjha1)
- **Devesh Jha** (@deveshjha247)

We welcome contributions from the community!

## License

This project is developed for public benefit.
