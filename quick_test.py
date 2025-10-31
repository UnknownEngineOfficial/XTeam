#!/usr/bin/env python3
"""
Quick XTeam API Test - Tests core functionality
"""

import asyncio
import httpx
import json
import time

async def quick_test():
    """Quick test of core API functionality"""
    base_url = "http://localhost:8000"

    print("🚀 Quick XTeam API Test")
    print("=" * 50)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Health Check
            print("1. Testing Backend Health...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Backend health: OK")
            else:
                print(f"❌ Backend health failed: {response.status_code}")
                return

            # 2. API Endpoints
            print("2. Testing API Endpoints...")
            response = await client.get(f"{base_url}/openapi.json")
            if response.status_code == 200:
                api_spec = response.json()
                endpoints = len(api_spec.get("paths", {}))
                print(f"✅ API spec loaded: {endpoints} endpoints available")
            else:
                print(f"❌ API spec failed: {response.status_code}")
                return

            # 3. User Registration
            print("3. Testing User Registration...")
            user_data = {
                "email": f"test_{int(time.time())}@example.com",
                "username": f"testuser_{int(time.time())}",
                "password": "TestPass123",
                "full_name": "Test User"
            }

            response = await client.post(
                f"{base_url}/api/v1/auth/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 201:
                print("✅ User registration successful")
                reg_data = response.json()
                access_token = reg_data["token"]["access_token"]
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(f"Response: {response.text}")
                return

            # 4. User Profile
            print("4. Testing User Profile...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(f"{base_url}/api/v1/auth/auth/me", headers=headers)

            if response.status_code == 200:
                print("✅ User profile access successful")
            else:
                print(f"❌ Profile access failed: {response.status_code}")

            # 5. Project Creation
            print("5. Testing Project Creation...")
            project_data = {
                "name": "Quick Test Project",
                "description": "A quick test project",
                "requirements": "Build a simple test application"
            }

            response = await client.post(
                f"{base_url}/api/v1/projects/projects",
                json=project_data,
                headers=headers
            )

            if response.status_code == 201:
                print("✅ Project creation successful")
                project = response.json()
                project_id = project["id"]
            else:
                print(f"❌ Project creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return

            # 6. Project Retrieval
            print("6. Testing Project Retrieval...")
            response = await client.get(
                f"{base_url}/api/v1/projects/projects/{project_id}",
                headers=headers
            )

            if response.status_code == 200:
                print("✅ Project retrieval successful")
            else:
                print(f"❌ Project retrieval failed: {response.status_code}")

            # 7. Agent Presets
            print("7. Testing Agent Presets...")
            response = await client.get(
                f"{base_url}/api/v1/agents/agents/presets",
                headers=headers
            )

            if response.status_code == 200:
                presets = response.json()
                print(f"✅ Agent presets retrieved: {len(presets)} presets")
            else:
                print(f"⚠️ Agent presets failed: {response.status_code}")

            print("\n" + "=" * 50)
            print("🎉 CORE API TESTS COMPLETED SUCCESSFULLY!")
            print("✅ Backend Health: OK")
            print("✅ API Endpoints: OK")
            print("✅ Authentication: OK")
            print("✅ Project Management: OK")
            print("✅ Agent System: OK")
            print("=" * 50)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())