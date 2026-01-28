"""
Quick Example: How to use Self-Learning AI System
"""

import asyncio
from ai_learning_system import SelfLearningAI
from openai import OpenAI
from motor.motor_asyncio import AsyncIOMotorClient

async def example_usage():
    # Setup
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client['digital_sahayak']
    openai_client = OpenAI(api_key="your_key")
    
    ai = SelfLearningAI(openai_client, db)
    
    # Example 1: Learn from GitHub Copilot
    print("=" * 50)
    print("Example 1: Learning from GitHub Copilot")
    print("=" * 50)
    
    result = await ai.learn_from_other_ai(
        prompt="How to match jobs with user profile?",
        other_ai_response="""
        You can match jobs by comparing education level, age, and location.
        Use a scoring system to rank matches.
        """,
        ai_name="GitHub Copilot"
    )
    
    print("Analysis:")
    print(f"Strengths: {result['analysis']['strengths']}")
    print(f"Weaknesses: {result['analysis']['weaknesses']}")
    print(f"\nImproved Response:\n{result['improved_response']}")
    
    # Example 2: Generate with Learning
    print("\n" + "=" * 50)
    print("Example 2: Smart Generation")
    print("=" * 50)
    
    result = await ai.generate_with_learning(
        prompt="Generate job recommendations for a 25-year-old graduate",
        context="User prefers government jobs in Bihar"
    )
    
    print(f"Response: {result['response']}")
    print(f"Learnings Applied: {result['learnings_applied']}")
    print(f"Confidence: {result['confidence']}")
    
    # Example 3: Batch Compare
    print("\n" + "=" * 50)
    print("Example 3: Batch Learning")
    print("=" * 50)
    
    comparisons = [
        {
            "ai_name": "GitHub Copilot",
            "prompt": "Best way to store user preferences?",
            "response": "Use MongoDB with indexed fields"
        },
        {
            "ai_name": "ChatGPT",
            "prompt": "Best way to store user preferences?",
            "response": "Use PostgreSQL with proper normalization"
        }
    ]
    
    result = await ai.compare_and_learn_batch(comparisons)
    print(f"Patterns Learned: {result}")
    
    # Example 4: Get Stats
    print("\n" + "=" * 50)
    print("Example 4: Learning Statistics")
    print("=" * 50)
    
    stats = await ai.get_learning_stats()
    print(f"Total Learnings: {stats['total_learnings']}")
    print(f"Average Improvement: {stats['average_improvement_score']}%")
    print(f"Learning Rate: {stats['learning_rate']}")

if __name__ == "__main__":
    asyncio.run(example_usage())
