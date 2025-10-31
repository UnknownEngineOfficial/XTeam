#!/usr/bin/env python3
"""
Test script for XTeam API endpoints
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_registration():
    """Test user registration"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "TestPass123",
                    "full_name": "Test User"
                },
                headers={"Content-Type": "application/json"}
            )
            print(f"Registration status: {response.status_code}")
            print(f"Registration response: {response.text}")
            return response.json() if response.status_code == 201 else None
        except Exception as e:
            print(f"Registration failed: {e}")
            return None

async def test_login():
    """Test user login"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPass123"
                },
                headers={"Content-Type": "application/json"}
            )
            print(f"Login status: {response.status_code}")
            print(f"Login response: {response.text}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Login failed: {e}")
            return None

async def test_create_project(access_token):
    """Test project creation"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/projects/projects",
                json={
                    "name": "Test AI Chat App",
                    "description": "A test multi-agent AI chat application",
                    "requirements": "Build a simple chat interface with real-time messaging"
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
            )
            print(f"Create project status: {response.status_code}")
            print(f"Create project response: {response.text}")
            return response.json() if response.status_code == 201 else None
        except Exception as e:
            print(f"Create project failed: {e}")
            return None

async def test_execute_workflow(access_token, project_id):
    """Test workflow execution"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/projects/projects/{project_id}/execute?prompt=Build a simple REST API with user management&execution_type=full",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )
            print(f"Execute workflow status: {response.status_code}")
            print(f"Execute workflow response: {response.text}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Execute workflow failed: {e}")
            return None

async def main():
    print("Testing XTeam API endpoints...")

    # Test registration
    print("\n1. Testing user registration...")
    reg_result = await test_registration()
    if not reg_result:
        print("Registration failed, exiting...")
        return

    # Test login
    print("\n2. Testing user login...")
    login_result = await test_login()
    if not login_result:
        print("Login failed, exiting...")
        return

    access_token = login_result["token"]["access_token"]
    print(f"Got access token: {access_token[:20]}...")

    # Test project creation
    print("\n3. Testing project creation...")
    project_result = await test_create_project(access_token)
    if not project_result:
        print("Project creation failed, exiting...")
        return

    project_id = project_result["id"]
    print(f"Created project with ID: {project_id}")

    # Test workflow execution
    print("\n4. Testing workflow execution...")
    workflow_result = await test_execute_workflow(access_token, project_id)
    if workflow_result:
        print("Workflow execution started successfully!")
    else:
        print("Workflow execution failed")

    print("\nAPI testing completed!")

if __name__ == "__main__":
    asyncio.run(main())