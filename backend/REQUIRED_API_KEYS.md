# 🔑 Required API Keys for Job Recommendations

## 🚀 **Option 1: RapidAPI (RECOMMENDED - Easiest Setup)**

### **What You Need:**
1. **RapidAPI Account**: Free at https://rapidapi.com
2. **RapidAPI Key**: Get from your RapidAPI dashboard
3. **Job Search API**: Use "JSearch" API (free tier available)

### **Setup Steps:**
1. Go to https://rapidapi.com
2. Sign up for free account
3. Search for "JSearch" API
4. Subscribe to free plan
5. Copy your RapidAPI key

### **Environment Variable to Add:**
```
RAPID_API_KEY=your_rapidapi_key_here
```

### **Cost:** FREE tier available (100 requests/month)

---

## 🔗 **Option 2: LinkedIn API (Advanced)**

### **What You Need:**
1. **LinkedIn Developer Account**: https://developer.linkedin.com
2. **LinkedIn App**: Create a new app
3. **API Access**: Request access to LinkedIn Jobs API
4. **OAuth 2.0 Setup**: Configure authentication

### **Environment Variable:**
```
LINKEDIN_API_KEY=your_linkedin_api_key_here
```

### **Cost:** Free but requires approval process

---

## 💼 **Option 3: Indeed API (Alternative)**

### **What You Need:**
1. **Indeed Publisher Account**: https://www.indeed.com/publisher
2. **API Access**: Request access to Indeed API
3. **Publisher ID**: Get from Indeed dashboard

### **Environment Variable:**
```
INDEED_API_KEY=your_indeed_api_key_here
```

### **Cost:** Free for approved publishers

---

## 🎯 **RECOMMENDATION: Start with RapidAPI**

**Why RapidAPI is best for you:**
- ✅ **Instant setup** (5 minutes)
- ✅ **Free tier available**
- ✅ **Multiple job sources** (Indeed, LinkedIn, Glassdoor, etc.)
- ✅ **No approval process**
- ✅ **Reliable and well-documented**

---

## 🔧 **How to Add API Keys to Railway:**

1. Go to your Railway dashboard
2. Select your backend project
3. Go to "Variables" tab
4. Add the environment variable:
   - **Name:** `RAPID_API_KEY`
   - **Value:** Your RapidAPI key
5. Click "Add Variable"
6. Railway will automatically redeploy

---

## 🧪 **Testing Your API Key:**

Once you add the API key, the job recommendations will automatically switch from mock data to real job listings from:
- Indeed
- LinkedIn  
- Glassdoor
- ZipRecruiter
- And more...

---

## 📊 **Current Status:**

- ✅ **Backend**: Ready to use real APIs
- ✅ **Frontend**: Ready to display real jobs
- ✅ **Database**: Ready to store job data
- ⏳ **API Keys**: Need to be added to Railway

**Next Step:** Get a RapidAPI key and add it to your Railway environment variables! 