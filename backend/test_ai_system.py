"""
Quick Test Script for Self-Learning AI System
Run this to verify the AI system is working correctly
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000/api"
TOKEN = "your_jwt_token_here"  # Get from login

async def test_ai_system():
    """Test all AI endpoints"""
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Testing Self-Learning AI System")
        print("=" * 60)
        
        # Test 1: Get Project Context
        print("\n1️⃣ Testing: Get Project Context")
        try:
            response = await client.get(
                f"{BASE_URL}/ai/project-context",
                headers=headers
            )
            data = response.json()
            print(f"✅ Project Domain: {data['domain']['name']}")
            print(f"✅ Analyzed: {data['analyzed']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Web Search
        print("\n2️⃣ Testing: Web Search")
        try:
            response = await client.post(
                f"{BASE_URL}/ai/web-search",
                headers=headers,
                json={
                    "query": "Indian government job latest updates 2026",
                    "max_results": 3
                }
            )
            data = response.json()
            print(f"✅ Found {data['count']} results")
            for idx, result in enumerate(data['results'], 1):
                print(f"   {idx}. {result['title'][:50]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Learn from External AI
        print("\n3️⃣ Testing: Learn from External AI")
        try:
            response = await client.post(
                f"{BASE_URL}/ai/learn-from-external",
                headers=headers,
                json={
                    "prompt": "How to improve job matching algorithm?",
                    "other_ai_response": "You can improve job matching by using machine learning algorithms to analyze user preferences and job requirements. Consider factors like education, location, and experience.",
                    "ai_name": "Test AI",
                    "use_web_search": False
                }
            )
            data = response.json()
            if data.get('success'):
                print("✅ Learning successful")
                print(f"   Strengths: {len(data['analysis']['strengths'])} identified")
                print(f"   Weaknesses: {len(data['analysis']['weaknesses'])} identified")
                print(f"   Improved response generated: {len(data['improved_response'])} chars")
            else:
                print(f"❌ Learning failed: {data.get('error')}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Smart Generation
        print("\n4️⃣ Testing: Smart Generation")
        try:
            response = await client.post(
                f"{BASE_URL}/ai/generate-smart",
                headers=headers,
                json={
                    "prompt": "Recommend best jobs for a 25-year-old graduate from Bihar",
                    "use_web_search": False
                }
            )
            data = response.json()
            print(f"✅ Response generated")
            print(f"   Learnings applied: {data['learnings_applied']}")
            print(f"   Confidence: {data['confidence']*100:.0f}%")
            print(f"   Response length: {len(data['response'])} chars")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Learning Stats
        print("\n5️⃣ Testing: Learning Statistics")
        try:
            response = await client.get(
                f"{BASE_URL}/ai/learning-stats",
                headers=headers
            )
            data = response.json()
            print(f"✅ Total Learnings: {data['total_learnings']}")
            print(f"✅ Avg Improvement: {data['average_improvement_score']:.1f}%")
            print(f"✅ Learning Rate: {data['learning_rate']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("Testing Complete!")
        print("=" * 60)

if __name__ == "__main__":
    print("\n🚀 Starting AI System Tests...")
    print("Note: Make sure backend server is running on port 8000")
    print("Note: Replace TOKEN variable with your JWT token\n")
    
    asyncio.run(test_ai_system())
