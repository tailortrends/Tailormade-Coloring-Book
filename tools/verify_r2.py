#!/usr/bin/env python3
"""
Cloudflare R2 Connection Verification Script

Tests R2 object storage connectivity, upload, download, and public URL access.

Usage:
    python tools/verify_r2.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


def get_r2_config():
    """Load R2 configuration from environment."""
    from dotenv import load_dotenv
    
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    load_dotenv(env_path)
    
    config = {
        "account_id": os.getenv("R2_ACCOUNT_ID"),
        "access_key_id": os.getenv("R2_ACCESS_KEY_ID"),
        "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY"),
        "bucket_name": os.getenv("R2_BUCKET_NAME"),
        "public_url": os.getenv("R2_PUBLIC_URL")
    }
    
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"❌ Missing R2 configuration: {', '.join(missing)}")
        print("   Please check backend/.env file")
        sys.exit(1)
    
    return config


def get_r2_client(config):
    """Create S3-compatible R2 client."""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=config['access_key_id'],
        aws_secret_access_key=config['secret_access_key'],
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )


def verify_connection(client, config):
    """Verify basic R2 connection."""
    print("\n🔌 Testing R2 Connection...")
    
    try:
        # Try to head the bucket
        client.head_bucket(Bucket=config['bucket_name'])
        print(f"  ✅ Successfully connected to bucket: {config['bucket_name']}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"  ❌ Bucket '{config['bucket_name']}' does not exist")
        elif error_code == '403':
            print(f"  ❌ Access denied to bucket '{config['bucket_name']}'")
        else:
            print(f"  ❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def verify_upload(client, config):
    """Test file upload to R2."""
    print("\n⬆️  Testing File Upload...")
    
    try:
        # Create test file content
        test_key = f"_health_check/test_{datetime.now().isoformat()}.txt"
        test_content = f"R2 Health Check - {datetime.now().isoformat()}"
        
        # Upload test file
        client.put_object(
            Bucket=config['bucket_name'],
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType="text/plain"
        )
        print(f"  ✅ File uploaded successfully: {test_key}")
        
        return test_key
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return None


def verify_download(client, config, test_key):
    """Test file download from R2."""
    print("\n⬇️  Testing File Download...")
    
    if not test_key:
        print("  ⚠️  Skipped (upload failed)")
        return False
    
    try:
        # Download test file
        response = client.get_object(
            Bucket=config['bucket_name'],
            Key=test_key
        )
        content = response['Body'].read().decode('utf-8')
        print(f"  ✅ File downloaded successfully")
        print(f"  ℹ️  Content: {content[:50]}...")
        
        return True
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return False


def verify_public_url(config, test_key):
    """Verify public URL access."""
    print("\n🌐 Testing Public URL...")
    
    if not test_key:
        print("  ⚠️  Skipped (upload failed)")
        return False
    
    try:
        import requests
        
        public_url = f"{config['public_url']}/{test_key}"
        print(f"  ℹ️  Testing URL: {public_url}")
        
        response = requests.get(public_url, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✅ Public URL accessible")
            print(f"  ℹ️  Content length: {len(response.content)} bytes")
            return True
        else:
            print(f"  ❌ URL returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Public URL test failed: {e}")
        return False


def cleanup(client, config, test_key):
    """Clean up test file."""
    print("\n🧹 Cleaning Up...")
    
    if not test_key:
        print("  ⚠️  No cleanup needed")
        return True
    
    try:
        client.delete_object(
            Bucket=config['bucket_name'],
            Key=test_key
        )
        print(f"  ✅ Test file deleted: {test_key}")
        return True
    except Exception as e:
        print(f"  ⚠️  Cleanup failed (non-critical): {e}")
        return False


def main():
    """Run all R2 verification tests."""
    print("=" * 60)
    print("☁️  Cloudflare R2 Connection Verification")
    print("=" * 60)
    
    # Load configuration
    print("\n📋 Loading Configuration...")
    config = get_r2_config()
    print(f"  ✅ Configuration loaded")
    print(f"  ℹ️  Bucket: {config['bucket_name']}")
    print(f"  ℹ️  Public URL: {config['public_url']}")
    
    # Create R2 client
    print("\n🔧 Creating R2 Client...")
    try:
        client = get_r2_client(config)
        print("  ✅ Client created")
    except Exception as e:
        print(f"  ❌ Failed to create client: {e}")
        sys.exit(1)
    
    # Run tests
    test_key = None
    results = {}
    
    results["Connection"] = verify_connection(client, config)
    
    if results["Connection"]:
        test_key = verify_upload(client, config)
        results["Upload"] = test_key is not None
        results["Download"] = verify_download(client, config, test_key)
        results["Public URL"] = verify_public_url(config, test_key)
        results["Cleanup"] = cleanup(client, config, test_key)
    else:
        print("\n⚠️  Skipping remaining tests (connection failed)")
    
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
        print("✅ All R2 tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some R2 tests failed. Please review errors above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
