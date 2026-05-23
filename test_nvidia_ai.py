"""Test NVIDIA GLM4.7 API connection."""
import asyncio
from ai.ai_client import get_ai_client


async def test_nvidia_ai():
    """Test NVIDIA GLM4.7 API connection."""
    client = get_ai_client()
    
    try:
        response = await client.chat_completion(
            messages=[
                {"role": "user", "content": "speak with me in english"}
            ],
            model="z-ai/glm4.7",
            temperature=1,
            max_tokens=16384,
        )
        print("✅ NVIDIA GLM4.7 API is working!")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_nvidia_ai())
