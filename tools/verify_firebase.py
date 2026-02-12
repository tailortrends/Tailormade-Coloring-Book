#!/usr/bin/env python3
"""
Firebase Connection Verification Script

Tests Firebase Auth and Firestore connectivity.
Verifies service account credentials and basic operations.

Usage:
    python tools/verify_firebase.py
"""

import sys
import os
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from firebase_admin import credentials, auth, firestore, initialize_app


def verify_firebase_auth():
    """Verify Firebase Auth configuration and service account."""
    print("\n🔐 Testing Firebase Auth...")
    
    try:
        # Get service account info
        cred = credentials.ApplicationDefault()
        print("  ✅ Service account credentials loaded")
        
        # Try listing users (will fail if permissions invalid)
        users = auth.list_users(max_results=1)
        print(f"  ✅ Successfully connected to Firebase Auth")
        print(f"  ℹ️  Total users in system: {len(list(users.iterate_all()))}")
        
        return True
    except Exception as e:
        print(f"  ❌ Firebase Auth test failed: {e}")
        return False


def verify_firestore():
    """Verify Firestore database connectivity."""
    print("\n📊 Testing Firestore...")
    
    try:
        db = firestore.client()
        
        # Test write operation
        test_ref = db.collection("_health_check").document("test")
        test_ref.set({
            "timestamp": firestore.SERVER_TIMESTAMP,
            "status": "healthy",
            "source": "verify_firebase.py"
        })
        print("  ✅ Write operation successful")
        
        # Test read operation
        doc = test_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"  ✅ Read operation successful")
            print(f"  ℹ️  Document data: {data}")
        else:
            print("  ⚠️  Document not found after write")
            return False
        
        # Clean up test document
        test_ref.delete()
        print("  ✅ Cleanup successful")
        
        return True
    except Exception as e:
        print(f"  ❌ Firestore test failed: {e}")
        return False


def verify_collections():
    """Verify expected Firestore collections exist."""
    print("\n📂 Checking Firestore Collections...")
    
    try:
        db = firestore.client()
        
        # Expected collections
        expected = ["users", "books"]
        
        for collection_name in expected:
            collection_ref = db.collection(collection_name)
            # Try to get first document
            docs = list(collection_ref.limit(1).stream())
            
            if docs:
                print(f"  ✅ Collection '{collection_name}' exists with documents")
            else:
                print(f"  ⚠️  Collection '{collection_name}' exists but is empty")
        
        return True
    except Exception as e:
        print(f"  ❌ Collection check failed: {e}")
        return False


def main():
    """Run all Firebase verification tests."""
    print("=" * 60)
    print("🔥 Firebase Connection Verification")
    print("=" * 60)
    
    # Check for service account file
    service_account_path = Path(__file__).parent.parent / "tailormade-coloring-book-firebase-adminsdk-fbsvc-8f5c806460.json"
    
    if not service_account_path.exists():
        print(f"\n❌ Service account file not found at: {service_account_path}")
        print("   Please ensure Firebase credentials are configured.")
        sys.exit(1)
    
    print(f"\n📄 Service account file found: {service_account_path.name}")
    
    # Initialize Firebase
    try:
        cred = credentials.Certificate(str(service_account_path))
        initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        sys.exit(1)
    
    # Run tests
    results = {
        "Firebase Auth": verify_firebase_auth(),
        "Firestore": verify_firestore(),
        "Collections": verify_collections()
    }
    
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
        print("✅ All Firebase tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some Firebase tests failed. Please review errors above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
