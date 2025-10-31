#!/usr/bin/env python3
"""
Backend-Only XTeam Platform Test Suite
Tests backend components without interfering with frontend server
"""

import asyncio
import httpx
import json
import websockets
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackendTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.test_results = {
            "backend_health": False,
            "authentication": False,
            "project_management": False,
            "agent_configuration": False,
            "workflow_execution": False,
            "websocket_communication": False,
            "api_endpoints": False
        }
        self.access_token = None
        self.test_user = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123",
            "full_name": "Test User"
        }
        self.test_project = None

    async def run_backend_tests(self) -> Dict:
        """Run backend-focused test suite"""
        logger.info("🚀 Starting XTeam Backend Test Suite")

        try:
            # 1. Backend Health Check
            await self.test_backend_health()

            # 2. API Endpoints Check
            await self.test_api_endpoints()

            # 3. Authentication Tests
            await self.test_authentication()

            # 4. Project Management Tests
            if self.access_token:
                await self.test_project_management()

            # 5. Agent Configuration Tests
            if self.access_token:
                await self.test_agent_configuration()

            # 6. Workflow Execution Tests
            if self.access_token and self.test_project:
                await self.test_workflow_execution()

            # 7. WebSocket Tests
            await self.test_websocket_communication()

        except Exception as e:
            logger.error(f"Backend test suite failed: {e}")

        return self.generate_backend_report()

    async def test_backend_health(self):
        """Test backend server health"""
        logger.info("🔍 Testing Backend Health...")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test root health endpoint
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ Backend health: {health_data}")
                    self.test_results["backend_health"] = True
                else:
                    logger.error(f"❌ Backend health check failed: {response.status_code}")
                    return

        except Exception as e:
            logger.error(f"❌ Backend health test failed: {e}")

    async def test_api_endpoints(self):
        """Test API endpoints availability"""
        logger.info("🔍 Testing API Endpoints...")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test OpenAPI spec
                response = await client.get(f"{self.base_url}/openapi.json")
                if response.status_code == 200:
                    openapi_spec = response.json()
                    paths = openapi_spec.get("paths", {})
                    logger.info(f"✅ API spec loaded: {len(paths)} endpoints available")

                    # Check key endpoints exist
                    required_endpoints = [
                        "/api/v1/auth/auth/register",
                        "/api/v1/auth/auth/login",
                        "/api/v1/projects/projects",
                        "/api/v1/agents/agents/presets"
                    ]

                    missing_endpoints = []
                    for endpoint in required_endpoints:
                        if endpoint not in paths:
                            missing_endpoints.append(endpoint)

                    if not missing_endpoints:
                        logger.info("✅ All required API endpoints available")
                        self.test_results["api_endpoints"] = True
                    else:
                        logger.warning(f"⚠️ Missing endpoints: {missing_endpoints}")

                else:
                    logger.error(f"❌ API spec not accessible: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ API endpoints test failed: {e}")

    async def test_authentication(self):
        """Test user registration and login"""
        logger.info("🔍 Testing Authentication...")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test registration
                register_data = self.test_user.copy()
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/auth/register",
                    json=register_data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 201:
                    logger.info("✅ User registration successful")
                    register_result = response.json()
                    self.access_token = register_result["token"]["access_token"]
                elif response.status_code == 400 and "already registered" in response.text.lower():
                    logger.info("ℹ️ User already exists, attempting login")
                    # Try login instead
                    login_data = {
                        "email": self.test_user["email"],
                        "password": self.test_user["password"]
                    }
                    response = await client.post(
                        f"{self.base_url}/api/v1/auth/auth/login",
                        json=login_data,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        logger.info("✅ User login successful")
                        login_result = response.json()
                        self.access_token = login_result["token"]["access_token"]
                    else:
                        logger.error(f"❌ Login failed: {response.status_code} - {response.text}")
                        return
                else:
                    logger.error(f"❌ Registration failed: {response.status_code} - {response.text}")
                    return

                # Test token validation
                if self.access_token:
                    response = await client.get(
                        f"{self.base_url}/api/v1/auth/auth/me",
                        headers={"Authorization": f"Bearer {self.access_token}"}
                    )

                    if response.status_code == 200:
                        user_data = response.json()
                        logger.info(f"✅ Token validation successful for user: {user_data.get('username')}")
                        self.test_results["authentication"] = True
                    else:
                        logger.error(f"❌ Token validation failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")

    async def test_project_management(self):
        """Test project CRUD operations"""
        logger.info("🔍 Testing Project Management...")

        if not self.access_token:
            logger.error("❌ No access token available")
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }

                # Create project
                project_data = {
                    "name": "Test AI Assistant",
                    "description": "A comprehensive test project for AI assistant functionality",
                    "requirements": "Build an AI assistant that can help with coding tasks, answer questions, and provide real-time collaboration features."
                }

                response = await client.post(
                    f"{self.base_url}/api/v1/projects/projects",
                    json=project_data,
                    headers=headers
                )

                if response.status_code == 201:
                    logger.info("✅ Project creation successful")
                    self.test_project = response.json()
                    project_id = self.test_project["id"]

                    # Get project details
                    response = await client.get(
                        f"{self.base_url}/api/v1/projects/projects/{project_id}",
                        headers=headers
                    )

                    if response.status_code == 200:
                        logger.info("✅ Project retrieval successful")
                    else:
                        logger.warning(f"⚠️ Project retrieval failed: {response.status_code}")

                    # Update project
                    update_data = {"progress": 25.0, "status": "active"}
                    response = await client.patch(
                        f"{self.base_url}/api/v1/projects/projects/{project_id}",
                        json=update_data,
                        headers=headers
                    )

                    if response.status_code == 200:
                        logger.info("✅ Project update successful")
                    else:
                        logger.warning(f"⚠️ Project update failed: {response.status_code}")

                    # List projects
                    response = await client.get(
                        f"{self.base_url}/api/v1/projects/projects",
                        headers=headers
                    )

                    if response.status_code == 200:
                        projects = response.json()
                        logger.info(f"✅ Project listing successful: {len(projects.get('items', []))} projects found")
                        self.test_results["project_management"] = True
                    else:
                        logger.warning(f"⚠️ Project listing failed: {response.status_code}")

                else:
                    logger.error(f"❌ Project creation failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"❌ Project management test failed: {e}")

    async def test_agent_configuration(self):
        """Test agent configuration endpoints"""
        logger.info("🔍 Testing Agent Configuration...")

        if not self.access_token:
            logger.error("❌ No access token available")
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }

                # Get agent presets
                response = await client.get(
                    f"{self.base_url}/api/v1/agents/agents/presets",
                    headers=headers
                )

                if response.status_code == 200:
                    presets = response.json()
                    logger.info(f"✅ Agent presets retrieved: {len(presets)} presets available")

                    # Test configuration validation
                    config_data = {
                        "agent_role": "architect",
                        "llm_provider": "openai",
                        "llm_model": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }

                    response = await client.post(
                        f"{self.base_url}/api/v1/agents/agents/validate",
                        json=config_data,
                        headers=headers
                    )

                    if response.status_code == 200:
                        validation = response.json()
                        if validation.get("valid", False):
                            logger.info("✅ Agent configuration validation successful")
                            self.test_results["agent_configuration"] = True
                        else:
                            logger.warning(f"⚠️ Configuration validation failed: {validation.get('errors', [])}")
                    else:
                        logger.warning(f"⚠️ Configuration validation request failed: {response.status_code}")

                else:
                    logger.warning(f"⚠️ Agent presets retrieval failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Agent configuration test failed: {e}")

    async def test_workflow_execution(self):
        """Test MetaGPT workflow execution"""
        logger.info("🔍 Testing Workflow Execution...")

        if not self.access_token or not self.test_project:
            logger.error("❌ Missing access token or test project")
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                project_id = self.test_project["id"]

                # Execute workflow
                response = await client.post(
                    f"{self.base_url}/api/v1/projects/projects/{project_id}/execute?prompt=Design and implement a simple task management API&execution_type=full",
                    headers=headers
                )

                if response.status_code == 200:
                    execution_result = response.json()
                    logger.info("✅ Workflow execution started successfully")
                    logger.info(f"Execution details: {execution_result}")

                    # Wait a bit for workflow to process
                    await asyncio.sleep(5)

                    # Check project status after execution
                    response = await client.get(
                        f"{self.base_url}/api/v1/projects/projects/{project_id}",
                        headers=headers
                    )

                    if response.status_code == 200:
                        updated_project = response.json()
                        logger.info(f"✅ Project status after execution: {updated_project.get('status')}")
                        self.test_results["workflow_execution"] = True
                    else:
                        logger.warning(f"⚠️ Could not check project status after execution: {response.status_code}")

                else:
                    logger.error(f"❌ Workflow execution failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"❌ Workflow execution test failed: {e}")

    async def test_websocket_communication(self):
        """Test WebSocket real-time communication"""
        logger.info("🔍 Testing WebSocket Communication...")

        try:
            # Connect to WebSocket
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("✅ WebSocket connection established")

                # Send a test message
                test_message = {
                    "type": "ping",
                    "data": {"message": "test"},
                    "timestamp": time.time()
                }

                await websocket.send(json.dumps(test_message))
                logger.info("✅ Test message sent via WebSocket")

                # Try to receive response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"✅ WebSocket response received: {response}")
                    self.test_results["websocket_communication"] = True
                except asyncio.TimeoutError:
                    logger.warning("⚠️ No WebSocket response received within timeout")

        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")

    def generate_backend_report(self) -> Dict:
        """Generate backend-focused test report"""
        logger.info("📊 Generating Backend Test Report...")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_tests / total_tests) * 100

        report = {
            "timestamp": time.time(),
            "test_type": "backend_only",
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "test_results": self.test_results,
            "system_info": {
                "backend_url": self.base_url,
                "websocket_url": self.ws_url,
                "test_user": self.test_user["email"]
            },
            "recommendations": self.generate_recommendations(),
            "issues_found": self.identify_issues()
        }

        return report

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        if not self.test_results["backend_health"]:
            recommendations.append("🔧 Fix backend server startup issues")
        if not self.test_results["api_endpoints"]:
            recommendations.append("🔧 Complete API endpoint implementation")
        if not self.test_results["authentication"]:
            recommendations.append("🔧 Implement or fix authentication endpoints")
        if not self.test_results["project_management"]:
            recommendations.append("🔧 Complete project management API implementation")
        if not self.test_results["agent_configuration"]:
            recommendations.append("🔧 Implement agent configuration management")
        if not self.test_results["workflow_execution"]:
            recommendations.append("🔧 Fix MetaGPT workflow execution")
        if not self.test_results["websocket_communication"]:
            recommendations.append("🔧 Implement WebSocket real-time communication")

        if not recommendations:
            recommendations.append("✅ All backend systems operational")

        return recommendations

    def identify_issues(self) -> List[str]:
        """Identify specific issues found during testing"""
        issues = []

        failed_tests = [test for test, result in self.test_results.items() if not result]

        for test in failed_tests:
            issues.append(f"❌ {test.replace('_', ' ').title()} functionality not working")

        if not issues:
            issues.append("✅ No critical backend issues found")

        return issues

async def main():
    """Main backend test execution"""
    test_suite = BackendTestSuite()
    report = await test_suite.run_backend_tests()

    # Print formatted report
    print("\n" + "="*80)
    print("🎯 XTEAM BACKEND COMPREHENSIVE TEST REPORT")
    print("="*80)

    print(f"\n📊 Test Summary:")
    print(f"   Total Tests: {report['test_summary']['total_tests']}")
    print(f"   Passed: {report['test_summary']['passed_tests']}")
    print(f"   Failed: {report['test_summary']['failed_tests']}")
    print(f"   Success Rate: {report['test_summary']['success_rate']}")

    print(f"\n🔍 Test Results:")
    for test, result in report['test_results'].items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test.replace('_', ' ').title()}: {status}")

    print(f"\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"   {rec}")

    print(f"\n⚠️ Issues Found:")
    for issue in report['issues_found']:
        print(f"   {issue}")

    print(f"\n🔗 System Information:")
    print(f"   Backend: {report['system_info']['backend_url']}")
    print(f"   WebSocket: {report['system_info']['websocket_url']}")
    print(f"   Test User: {report['system_info']['test_user']}")

    print("\n" + "="*80)

    # Save detailed report to file
    with open("/workspaces/XTeam/backend_test_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("📄 Detailed backend report saved to: /workspaces/XTeam/backend_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())