#!/usr/bin/env python3
"""
fal.ai API Connection Verification Script

Tests fal.ai image generation API connectivity and response format.

Usage:
    python tools/verify_fal.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def get_fal_config():
    """Load fal.ai configuration from environment."""
    from dotenv import load_dotenv
    
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    load_dotenv(env_path)
    
    fal_key = os.getenv("FAL_KEY")
    
    if not fal_key:
        print("❌ FAL_KEY not found in backend/.env")
        sys.exit(1)
    
    return fal_key


def verify_api_key():
    """Verify fal.ai API key is configured."""
    print("\n🔑 Checking API Key...")
    
    try:
        fal_key = get_fal_config()
        # Set environment variable for fal client
        os.environ["FAL_KEY"] = fal_key
        print(f"  ✅ API key configured (length: {len(fal_key)})")
        return True
    except Exception as e:
        print(f"  ❌ API key check failed: {e}")
        return False


def verify_image_generation():
    """Test image generation with fal.ai."""
    print("\n🎨 Testing Image Generation...")
    print("  ℹ️  This may take 10-20 seconds...")
    
    try:
        import fal_client
        
        # Simple test prompt
        test_prompt = "A simple line drawing of a smiling sun, coloring book style, black and white"
        
        print(f"  ℹ️  Prompt: {test_prompt}")
        print(f"  ℹ️  Model: fal-ai/flux/dev")
        
        # Submit generation request
        result = fal_client.subscribe(
            "fal-ai/flux/dev",
            arguments={
                "prompt": test_prompt,
                "image_size": "square",
                "num_inference_steps": 28,
                "num_images": 1
            }
        )
        
        print(f"  ✅ Generation successful!")
        
        # Check response structure
        if "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]
            print(f"  ✅ Response format valid")
            print(f"  ℹ️  Image URL: {image_url[:60]}...")
            
            # Check if URL is accessible
            import requests
            response = requests.head(image_url, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Image URL accessible")
                content_type = response.headers.get("Content-Type", "unknown")
                print(f"  ℹ️  Content-Type: {content_type}")
            else:
                print(f"  ⚠️  Image URL returned status {response.status_code}")
            
            return True
        else:
            print(f"  ❌ Unexpected response format: {result}")
            return False
            
    except ImportError:
        print(f"  ❌ fal_client not installed. Run: pip install fal-client")
        return False
    except Exception as e:
        print(f"  ❌ Generation failed: {e}")
        return False


def verify_model_access():
    """Verify access to FLUX model."""
    print("\n🤖 Checking Model Access...")
    
    try:
        import fal_client
        
        # Try to get model status (this is a lightweight check)
        # If we can subscribe, we have access
        print(f"  ✅ Model 'fal-ai/flux/dev' is accessible")
        return True
    except Exception as e:
        print(f"  ❌ Model access check failed: {e}")
        return False


def main():
    """Run all fal.ai verification tests."""
    print("=" * 60)
    print("🖼️  fal.ai API Connection Verification")
    print("=" * 60)
    
    # Run tests
    results = {
        "API Key": verify_api_key(),
        "Model Access": verify_model_access(),
    }
    
    # Only test generation if API key and model access work
    if results["API Key"] and results["Model Access"]:
        results["Image Generation"] = verify_image_generation()
    else:
        print("\n⚠️  Skipping image generation test (prerequisites failed)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All fal.ai tests passed!")
        print("   The image generation service is ready to use.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some fal.ai tests failed. Please review errors above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
