# Rezzy Backend

A FastAPI-powered backend service for AI-powered resume analysis and job matching.

## Features

- 🔐 **User Management**: Complete user registration and authentication
- 📄 **Resume Parsing**: AI-powered resume text extraction and analysis
- 💼 **Job Analysis**: Intelligent job description parsing and keyword extraction
- 🤖 **AI Evaluation**: OpenAI-powered resume-job matching analysis
- 💳 **Payment Processing**: Stripe integration for subscription management
- 📁 **File Storage**: AWS S3 integration for resume file storage
- 🗄️ **Database**: PostgreSQL with NeonDB for data persistence
- 📊 **Analytics**: Usage tracking and subscription management

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **Database**: PostgreSQL (NeonDB)
- **AI**: OpenAI GPT-4
- **Payments**: Stripe
- **Storage**: AWS S3
- **Authentication**: Clerk integration
- **Deployment**: Railway-ready

## API Endpoints

### User Management
- `POST /api/create-user` - Create new user
- `GET /api/get-plan` - Get user subscription plan
- `GET /api/resume-analyses` - Get user's saved analyses
- `GET /api/resume-analysis/{id}` - Get specific analysis

### Resume Processing
- `POST /api/upload-resume` - Upload and parse resume
- `POST /api/analyze-job` - Analyze job description
- `POST /api/evaluate-resume` - AI-powered resume evaluation

### AI Features
- `POST /api/generate-cover-letter` - Generate cover letter
- `POST /api/generate-interview-questions` - Generate interview questions

### Payments
- `POST /api/create-checkout-session` - Create Stripe checkout session
- `POST /api/stripe-webhook` - Handle Stripe webhooks

### Health
- `GET /api/health` - Health check endpoint

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL database
- OpenAI API key
- Stripe account
- AWS S3 bucket
- Clerk account

### Installation

1. Clone the repository:
```bash
git clone <your-backend-repo-url>
cd rezzy_app
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env_template.txt .env
```

Add your environment variables:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DATABASE_URL=postgresql://username:password@host/database

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name

# Stripe Configuration
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
STRIPE_STARTER_PRICE_ID=your_starter_price_id
STRIPE_PREMIUM_PRICE_ID=your_premium_price_id

# Application Configuration
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000
```

5. Set up database:
```bash
python setup_neon_db.py
```

6. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `AWS_REGION` | AWS region | Yes |
| `AWS_S3_BUCKET_NAME` | S3 bucket name | Yes |
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | Yes |
| `STRIPE_STARTER_PRICE_ID` | Stripe starter price ID | Yes |
| `STRIPE_PREMIUM_PRICE_ID` | Stripe premium price ID | Yes |
| `ENVIRONMENT` | Environment (development/production) | Yes |
| `DEBUG` | Debug mode | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | Yes |

## Database Schema

### Users Table
- `id` (UUID) - Primary key
- `clerk_user_id` (String) - Clerk user ID
- `email` (String) - User email
- `first_name` (String) - First name
- `last_name` (String) - Last name
- `plan` (String) - Subscription plan
- `created_at` (Timestamp) - Creation time
- `updated_at` (Timestamp) - Last update time

### Resume Analyses Table
- `id` (Integer) - Primary key
- `user_id` (UUID) - Foreign key to users
- `resume_text` (Text) - Extracted resume text
- `job_description` (Text) - Job description
- `ai_evaluation` (JSON) - AI evaluation results
- `keyword_gaps` (JSON) - Keyword analysis
- `job_analysis` (JSON) - Job analysis results
- `created_at` (Timestamp) - Creation time

### Usage Table
- `id` (Integer) - Primary key
- `user_id` (UUID) - Foreign key to users
- `month` (String) - Month (YYYY-MM)
- `scans_used` (Integer) - Number of scans used
- `cover_letters_generated` (Integer) - Cover letters generated
- `interview_questions_generated` (Integer) - Interview questions generated

## Deployment

This application is designed to be deployed on Railway.

1. Push your code to GitHub
2. Connect your repository to Railway
3. Add environment variables in Railway dashboard
4. Deploy!

### Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Add environment variables
railway variables set OPENAI_API_KEY=your_key
railway variables set DATABASE_URL=your_db_url
# ... add all other variables

# Deploy
railway up
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Run tests
python -m pytest tests/

# Test specific endpoint
python test_payments.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. 