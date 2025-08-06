#!/usr/bin/env python3
"""
Test script to check if API keys are working
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_rapidapi():
    """Test RapidAPI connection"""
    print("🔍 Testing RapidAPI...")
    
    rapid_api_key = os.getenv('RAPID_API_KEY')
    if not rapid_api_key:
        print("❌ RAPID_API_KEY not found in environment variables")
        return False
    
    try:
        headers = {
            'X-RapidAPI-Key': rapid_api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
        
        params = {
            'query': 'software engineer',
            'location': 'San Francisco',
            'num_pages': '1',
            'page': '1'
        }
        
        response = requests.get(
            'https://jsearch.p.rapidapi.com/search',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('data', [])
            
            print(f"✅ RapidAPI working! Found {len(jobs)} jobs")
            
            if jobs:
                print("\n📋 Sample job:")
                job = jobs[0]
                print(f"   Title: {job.get('job_title', 'N/A')}")
                print(f"   Company: {job.get('employer_name', 'N/A')}")
                print(f"   Location: {job.get('job_city', 'N/A')}")
                print(f"   Salary: {job.get('job_salary', 'N/A')}")
            
            return True
        else:
            print(f"❌ RapidAPI error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RapidAPI test failed: {e}")
        return False

def test_linkedin_api():
    """Test LinkedIn API connection"""
    print("\n🔍 Testing LinkedIn API...")
    
    linkedin_api_key = os.getenv('LINKEDIN_API_KEY')
    if not linkedin_api_key:
        print("❌ LINKEDIN_API_KEY not found in environment variables")
        return False
    
    print("⚠️ LinkedIn API requires special setup and approval")
    print("   This is not currently implemented in the test")
    return False

def test_indeed_api():
    """Test Indeed API connection"""
    print("\n🔍 Testing Indeed API...")
    
    indeed_api_key = os.getenv('INDEED_API_KEY')
    if not indeed_api_key:
        print("❌ INDEED_API_KEY not found in environment variables")
        return False
    
    print("⚠️ Indeed API requires publisher approval")
    print("   This is not currently implemented in the test")
    return False

def main():
    """Run all API tests"""
    print("🚀 Testing API Keys for Job Recommendations")
    print("=" * 50)
    
    # Test each API
    rapidapi_working = test_rapidapi()
    linkedin_working = test_linkedin_api()
    indeed_working = test_indeed_api()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   RapidAPI: {'✅ Working' if rapidapi_working else '❌ Not working'}")
    print(f"   LinkedIn: {'✅ Working' if linkedin_working else '❌ Not working'}")
    print(f"   Indeed: {'✅ Working' if indeed_working else '❌ Not working'}")
    
    if rapidapi_working:
        print("\n🎉 Great! Your RapidAPI key is working.")
        print("   Job recommendations will show real data!")
    else:
        print("\n⚠️ No working API keys found.")
        print("   Job recommendations will show mock data.")
        print("\n💡 To get real job data:")
        print("   1. Get a RapidAPI key from https://rapidapi.com")
        print("   2. Add RAPID_API_KEY to your Railway environment variables")
        print("   3. Redeploy your backend")

if __name__ == "__main__":
    main() 