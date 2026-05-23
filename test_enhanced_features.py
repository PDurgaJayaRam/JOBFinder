"""
Test script for enhanced job matching features
Run this to verify everything is working correctly
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_ai_client():
    """Test multi-provider AI client"""
    print("\n" + "="*60)
    print("TEST 1: AI Client")
    print("="*60)
    
    try:
        from ai.multi_provider_client import ai_client
        
        print("Sending test message to AI...")
        response = ai_client.chat_complete(
            messages=[{"role": "user", "content": "Say 'Hello from AI!' in one sentence."}],
            max_tokens=50
        )
        
        print(f"✅ AI Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_job_matcher():
    """Test job matching engine"""
    print("\n" + "="*60)
    print("TEST 2: Job Matcher")
    print("="*60)
    
    try:
        from agents.job_matcher.matcher import job_matcher
        
        resume = {
            'skills': ['Python', 'FastAPI', 'React', 'SQL', 'Docker'],
            'experience_years': 3,
            'education': 'BS Computer Science',
            'experience': 'Built REST APIs and web applications'
        }
        
        job = {
            'title': 'Full Stack Developer',
            'company': 'Tech Corp',
            'description': 'We need a developer with Python, React, and 2+ years experience',
            'requirements': 'Python, React, SQL, Docker'
        }
        
        print("Calculating match score...")
        result = job_matcher.calculate_match_score(resume, job)
        
        print(f"\n✅ Match Results:")
        print(f"   Overall Score: {result['overall_score']}%")
        print(f"   Skill Score: {result['skill_score']}%")
        print(f"   Experience Score: {result['experience_score']}%")
        print(f"   Matched Skills: {', '.join(result['matched_skills'][:5])}")
        print(f"   Missing Skills: {', '.join(result['missing_skills'][:3])}")
        print(f"   Why Good Fit: {result['why_good_fit'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_generator():
    """Test custom resume generation"""
    print("\n" + "="*60)
    print("TEST 3: Resume Generator")
    print("="*60)
    
    try:
        from agents.resume_generator.generator import resume_generator
        
        resume = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'location': 'San Francisco, CA',
            'skills': ['Python', 'FastAPI', 'React', 'SQL', 'Docker'],
            'experience_years': 3,
            'current_role': 'Software Engineer',
            'experience': 'Built REST APIs using FastAPI. Developed React frontends. Managed PostgreSQL databases.',
            'education': 'BS Computer Science, Stanford University, 2020'
        }
        
        job = {
            'id': 999,
            'title': 'Senior Full Stack Developer',
            'company': 'Test_Corp',
            'requirements': 'Python, React, SQL, 3+ years experience',
            'description': 'We need a full stack developer with strong Python and React skills.'
        }
        
        match = {
            'matched_skills': ['Python', 'React', 'SQL'],
            'missing_skills': []
        }
        
        print("Generating custom resume...")
        filename = resume_generator.generate_custom_resume(resume, job, match)
        
        if os.path.exists(filename):
            print(f"✅ Resume generated: {filename}")
            print(f"   File size: {os.path.getsize(filename)} bytes")
            return True
        else:
            print(f"❌ Resume file not found: {filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test database tables"""
    print("\n" + "="*60)
    print("TEST 4: Database Tables")
    print("="*60)
    
    try:
        from database.engine import engine
        from database.models import JobMatch, CustomResume
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("Checking for new tables...")
        
        if 'job_matches' in tables:
            print("✅ job_matches table exists")
        else:
            print("❌ job_matches table missing - run create_new_tables.py")
            return False
        
        if 'custom_resumes' in tables:
            print("✅ custom_resumes table exists")
        else:
            print("❌ custom_resumes table missing - run create_new_tables.py")
            return False
        
        print(f"\nTotal tables in database: {len(tables)}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_api_keys():
    """Check if API keys are configured"""
    print("\n" + "="*60)
    print("PRE-CHECK: API Keys")
    print("="*60)
    
    mistral_key = os.getenv("MISTRAL_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if mistral_key:
        print(f"✅ MISTRAL_API_KEY found ({mistral_key[:10]}...)")
    else:
        print("⚠️  MISTRAL_API_KEY not found in .env")
    
    if gemini_key:
        print(f"✅ GEMINI_API_KEY found ({gemini_key[:10]}...)")
    else:
        print("⚠️  GEMINI_API_KEY not found in .env")
    
    if not mistral_key and not gemini_key:
        print("\n❌ No API keys configured!")
        print("Please add keys to .env file:")
        print("  MISTRAL_API_KEY=your_key_here")
        print("  GEMINI_API_KEY=your_key_here")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ENHANCED JOB MATCHING - TEST SUITE")
    print("="*60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API keys first
    if not check_api_keys():
        print("\n⚠️  Some tests may fail without API keys")
        print("Continue anyway? (y/n): ", end="")
        if input().lower() != 'y':
            return
    
    # Run tests
    results = {
        "AI Client": test_ai_client(),
        "Job Matcher": test_job_matcher(),
        "Resume Generator": test_resume_generator(),
        "Database": test_database(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your enhanced features are ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("Common fixes:")
        print("  1. Run: python install_dependencies.py")
        print("  2. Add API keys to .env file")
        print("  3. Run: python create_new_tables.py")


if __name__ == "__main__":
    main()
