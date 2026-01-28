import requests
import sys
import json
from datetime import datetime

class DigitalSahayakAPITester:
    def __init__(self, base_url="https://digitalsahayak.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.admin_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, use_admin=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use admin token if specified and available
        if use_admin and self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'
        elif self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        success, response = self.run_test(
            "Categories Endpoint",
            "GET",
            "categories",
            200
        )
        if success:
            print(f"   Found {len(response.get('job_categories', []))} job categories")
            print(f"   Found {len(response.get('yojana_categories', []))} yojana categories")
            print(f"   Found {len(response.get('states', []))} states")
        return success

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "name": f"Test User {timestamp}",
            "phone": f"9876543{timestamp[-3:]}",
            "password": "TestPass123!",
            "language": "hi"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   User registered with ID: {self.user_id}")
            return True
        return False

    def test_admin_login(self):
        """Test admin login with demo credentials"""
        admin_creds = {
            "phone": "6200184827",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=admin_creds
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            print(f"   Admin logged in with ID: {self.admin_user_id}")
            print(f"   Is Admin: {response['user'].get('is_admin', False)}")
            return True
        return False

    def test_user_profile(self):
        """Test getting user profile"""
        if not self.token:
            print("❌ Skipping - No user token available")
            return False
            
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_jobs_endpoints(self):
        """Test jobs-related endpoints"""
        # Test getting jobs
        success1, response1 = self.run_test(
            "Get Jobs List",
            "GET",
            "jobs",
            200
        )
        
        if success1:
            print(f"   Found {response1.get('total', 0)} jobs")
        
        # Test creating job (admin only)
        if not self.admin_token:
            print("❌ Skipping job creation - No admin token")
            return success1
            
        test_job = {
            "title": "Test Railway Job",
            "title_hi": "टेस्ट रेलवे नौकरी",
            "organization": "Indian Railways",
            "organization_hi": "भारतीय रेलवे",
            "description": "Test job description for railway recruitment",
            "description_hi": "रेलवे भर्ती के लिए टेस्ट नौकरी विवरण",
            "qualification": "10th Pass",
            "qualification_hi": "10वीं पास",
            "vacancies": 100,
            "salary": "18000-22000",
            "age_limit": "18-35",
            "last_date": "31 March 2025",
            "apply_link": "https://example.com/apply",
            "category": "railway",
            "state": "all"
        }
        
        success2, response2 = self.run_test(
            "Create Job (Admin)",
            "POST",
            "jobs",
            201,
            data=test_job,
            use_admin=True
        )
        
        return success1 and success2

    def test_yojana_endpoints(self):
        """Test yojana-related endpoints"""
        # Test getting yojanas
        success1, response1 = self.run_test(
            "Get Yojana List",
            "GET",
            "yojana",
            200
        )
        
        if success1:
            print(f"   Found {response1.get('total', 0)} yojanas")
        
        # Test creating yojana (admin only)
        if not self.admin_token:
            print("❌ Skipping yojana creation - No admin token")
            return success1
            
        test_yojana = {
            "name": "Test Housing Scheme",
            "name_hi": "टेस्ट आवास योजना",
            "ministry": "Ministry of Housing",
            "ministry_hi": "आवास मंत्रालय",
            "description": "Test housing scheme for eligible families",
            "description_hi": "पात्र परिवारों के लिए टेस्ट आवास योजना",
            "benefits": "Free housing assistance up to 2.5 lakhs",
            "benefits_hi": "2.5 लाख तक मुफ्त आवास सहायता",
            "eligibility": "Annual income below 3 lakhs",
            "eligibility_hi": "3 लाख से कम वार्षिक आय",
            "documents_required": ["Aadhaar Card", "Income Certificate", "Bank Passbook"],
            "apply_link": "https://example.com/housing-apply",
            "category": "housing",
            "state": "all",
            "govt_fee": 0,
            "service_fee": 20
        }
        
        success2, response2 = self.run_test(
            "Create Yojana (Admin)",
            "POST",
            "yojana",
            201,
            data=test_yojana,
            use_admin=True
        )
        
        return success1 and success2

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "admin/stats",
            200,
            use_admin=True
        )
        
        if success:
            print(f"   Total Users: {response.get('total_users', 0)}")
            print(f"   Total Jobs: {response.get('total_jobs', 0)}")
            print(f"   Total Yojanas: {response.get('total_yojana', 0)}")
            print(f"   Total Applications: {response.get('total_applications', 0)}")
            print(f"   Total Revenue: ₹{response.get('total_revenue', 0)}")
        
        return success

    def test_applications_flow(self):
        """Test application creation flow"""
        if not self.token:
            print("❌ Skipping - No user token available")
            return False
        
        # First get a job to apply for
        success, jobs_response = self.run_test(
            "Get Jobs for Application",
            "GET",
            "jobs?limit=1",
            200
        )
        
        if not success or not jobs_response.get('jobs'):
            print("❌ No jobs available for application test")
            return False
        
        job = jobs_response['jobs'][0]
        
        # Create application
        application_data = {
            "item_type": "job",
            "item_id": job['id'],
            "user_details": {
                "name": "Test Applicant",
                "phone": "9876543210",
                "email": "test@example.com",
                "address": "Test Address"
            },
            "documents": []
        }
        
        success, response = self.run_test(
            "Create Application",
            "POST",
            "applications",
            201,
            data=application_data
        )
        
        if success:
            print(f"   Application created with ID: {response.get('id')}")
            print(f"   Total fee: ₹{response.get('total_fee', 0)}")
        
        return success

    def test_whatsapp_endpoints(self):
        """Test WhatsApp endpoints (MOCK mode)"""
        if not self.admin_token:
            print("❌ Skipping WhatsApp tests - No admin token")
            return False
        
        # Test sending WhatsApp message (MOCK)
        message_data = {
            "phone": "9876543210",
            "message": "Test WhatsApp message from Digital Sahayak",
            "template": None
        }
        
        success, response = self.run_test(
            "Send WhatsApp Message (MOCK)",
            "POST",
            "whatsapp/send",
            200,
            data=message_data,
            use_admin=True
        )
        
        if success:
            print(f"   Message sent with ID: {response.get('message_id')}")
            print(f"   Status: {response.get('status')}")
        
        return success

    def test_job_scraping(self):
        """Test job scraping endpoint"""
        if not self.admin_token:
            print("❌ Skipping job scraping - No admin token")
            return False
        
        success, response = self.run_test(
            "Trigger Job Scraping",
            "POST",
            "admin/scrape-jobs",
            200,
            use_admin=True
        )
        
        if success:
            print(f"   Scraping status: {response.get('status')}")
            print(f"   Message: {response.get('message')}")
        
        return success

    def test_profile_preferences(self):
        """Test profile preferences update"""
        if not self.token:
            print("❌ Skipping profile preferences - No user token")
            return False
        
        # Update user preferences
        preferences_data = {
            "education_level": "graduate",
            "state": "bihar",
            "age": 25,
            "preferred_categories": ["government", "railway", "bank"]
        }
        
        success, response = self.run_test(
            "Update Profile Preferences",
            "PUT",
            "profile/preferences",
            200,
            data=preferences_data
        )
        
        if success:
            print(f"   Profile updated successfully")
            user_data = response.get('user', {})
            print(f"   Education: {user_data.get('education_level')}")
            print(f"   State: {user_data.get('state')}")
            print(f"   Age: {user_data.get('age')}")
            print(f"   Categories: {len(user_data.get('preferred_categories', []))}")
        
        return success

    def test_ai_recommendations(self):
        """Test AI job recommendations"""
        if not self.token:
            print("❌ Skipping AI recommendations - No user token")
            return False
        
        success, response = self.run_test(
            "Get AI Job Recommendations",
            "GET",
            "recommendations?limit=5",
            200
        )
        
        if success:
            recommendations = response.get('recommendations', [])
            print(f"   Found {len(recommendations)} recommendations")
            user_profile = response.get('user_profile', {})
            print(f"   User profile: Education={user_profile.get('education_level')}, State={user_profile.get('state')}, Age={user_profile.get('age')}")
            
            # Check if recommendations have match scores
            if recommendations:
                first_rec = recommendations[0]
                print(f"   First recommendation: {first_rec.get('title', 'N/A')}")
                print(f"   Match score: {first_rec.get('match_score', 'N/A')}%")
                if first_rec.get('ai_reason'):
                    print(f"   AI reason: {first_rec.get('ai_reason')[:50]}...")
        
        return success

    def test_matching_jobs(self):
        """Test matching jobs with scores"""
        if not self.token:
            print("❌ Skipping matching jobs - No user token")
            return False
        
        success, response = self.run_test(
            "Get Matching Jobs with Scores",
            "GET",
            "jobs/matching?limit=3",
            200
        )
        
        if success:
            jobs = response.get('jobs', [])
            print(f"   Found {len(jobs)} matching jobs")
            print(f"   Profile complete: {response.get('user_profile_complete', False)}")
            
            if jobs:
                for i, job in enumerate(jobs[:2]):
                    print(f"   Job {i+1}: {job.get('title', 'N/A')} - Score: {job.get('match_score', 'N/A')}%")
        
        return success

def main():
    print("🚀 Starting Digital Sahayak API Tests")
    print("=" * 50)
    
    tester = DigitalSahayakAPITester()
    
    # Test sequence
    tests = [
        ("Root API", tester.test_root_endpoint),
        ("Categories", tester.test_categories_endpoint),
        ("User Registration", tester.test_user_registration),
        ("Admin Login", tester.test_admin_login),
        ("User Profile", tester.test_user_profile),
        ("Jobs Endpoints", tester.test_jobs_endpoints),
        ("Yojana Endpoints", tester.test_yojana_endpoints),
        ("Admin Stats", tester.test_admin_stats),
        ("Applications Flow", tester.test_applications_flow),
        ("WhatsApp Endpoints", tester.test_whatsapp_endpoints),
        ("Job Scraping", tester.test_job_scraping),
        ("Profile Preferences", tester.test_profile_preferences),
        ("AI Recommendations", tester.test_ai_recommendations),
        ("Matching Jobs", tester.test_matching_jobs),
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())