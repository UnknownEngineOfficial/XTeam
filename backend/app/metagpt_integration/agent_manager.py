"""
Agent Manager

This module provides the AgentManager class for orchestrating MetaGPT agents
with custom LLM configurations per agent role.
"""

import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.project import Project
from app.models.execution import Execution, ExecutionStatus, ExecutionType
from app.models.agent_config import AgentRole
from app.services.agent_service import AgentService, get_agent_service
from app.metagpt_integration.llm_registry import get_llm_client_from_config

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Manager Class
# ============================================================================

class AgentManager:
    """
    Manager for orchestrating MetaGPT agents with custom LLM configurations.
    
    This class handles:
    - Agent initialization with per-role LLM configurations
    - Workflow execution and orchestration
    - Logging and streaming of agent outputs
    - Error handling and recovery
    """

    def __init__(
        self,
        db: AsyncSession,
        project: Project,
        user_id: str,
    ):
        """
        Initialize agent manager.
        
        Args:
            db: Database session
            project: Project instance
            user_id: User ID
        """
        self.db = db
        self.project = project
        self.user_id = user_id
        self.agent_service = get_agent_service(db)
        self.execution: Optional[Execution] = None
        self.agents: Dict[str, Any] = {}
        
        logger.info(f"Initialized AgentManager for project: {project.id}")

    # ========================================================================
    # Agent Initialization
    # ========================================================================

    async def initialize_agents(self) -> Dict[str, Any]:
        """
        Initialize all agents with custom LLM configurations.
        
        Returns:
            Dict[str, Any]: Dictionary of initialized agents
            
        Raises:
            ValueError: If agent configuration is invalid
        """
        logger.info("Initializing agents with custom LLM configurations")
        
        agents = {}
        
        # Define agent roles to initialize
        agent_roles = [
            AgentRole.PRODUCT_MANAGER,
            AgentRole.ARCHITECT,
            AgentRole.ENGINEER,
            AgentRole.QA_ENGINEER,
        ]
        
        for role in agent_roles:
            try:
                # Get agent configuration for this role
                config = await self.agent_service.get_agent_config_for_role(
                    self.user_id,
                    role,
                    use_default=True,
                )
                
                if not config:
                    logger.warning(f"No configuration found for role: {role.value}")
                    continue
                
                # Get LLM configuration
                llm_config = await self.agent_service.get_llm_config_for_agent(
                    self.user_id,
                    role,
                )
                
                # Create LLM client
                llm_client = get_llm_client_from_config(llm_config)
                
                # Validate connection
                is_valid = await llm_client.validate_connection()
                if not is_valid:
                    logger.error(f"Failed to validate LLM connection for role: {role.value}")
                    continue
                
                # Create agent instance (placeholder for actual MetaGPT agent)
                agent = {
                    "role": role.value,
                    "name": config.agent_name or role.value,
                    "llm_client": llm_client,
                    "config": config,
                    "llm_config": llm_config,
                }
                
                agents[role.value] = agent
                logger.info(f"Initialized agent: {role.value}")
                
            except Exception as e:
                logger.error(f"Failed to initialize agent {role.value}: {e}")
                continue
        
        self.agents = agents
        return agents

    # ========================================================================
    # Execution Management
    # ========================================================================

    async def create_execution(
        self,
        execution_type: ExecutionType = ExecutionType.FULL,
    ) -> Execution:
        """
        Create a new execution record.
        
        Args:
            execution_type: Type of execution
            
        Returns:
            Execution: Created execution instance
        """
        execution = Execution(
            project_id=self.project.id,
            user_id=self.user_id,
            execution_type=execution_type,
            status=ExecutionStatus.PENDING,
        )
        
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        self.execution = execution
        logger.info(f"Created execution: {execution.id}")
        
        return execution

    async def update_execution_status(
        self,
        status: ExecutionStatus,
    ) -> None:
        """
        Update execution status.
        
        Args:
            status: New status
        """
        if not self.execution:
            raise ValueError("No active execution")
        
        self.execution.status = status
        self.db.add(self.execution)
        await self.db.commit()
        
        logger.info(f"Updated execution status to: {status.value}")

    async def add_execution_log(
        self,
        agent: str,
        message: str,
        level: str = "info",
    ) -> None:
        """
        Add a log entry to the execution.
        
        Args:
            agent: Agent name
            message: Log message
            level: Log level (info, warning, error, debug)
        """
        if not self.execution:
            raise ValueError("No active execution")
        
        self.execution.add_log(agent, message, level)
        self.db.add(self.execution)
        await self.db.commit()

    async def set_execution_output(
        self,
        output: Dict[str, Any],
    ) -> None:
        """
        Set execution output.
        
        Args:
            output: Output dictionary
        """
        if not self.execution:
            raise ValueError("No active execution")
        
        self.execution.output = output
        self.db.add(self.execution)
        await self.db.commit()

    # ========================================================================
    # Workflow Execution
    # ========================================================================

    async def run_workflow(
        self,
        prompt: str,
        execution_type: ExecutionType = ExecutionType.FULL,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run a complete workflow with all agents.
        
        This is the main orchestration method that coordinates all agents
        to complete a project based on the provided prompt.
        
        Args:
            prompt: Project requirements/prompt
            execution_type: Type of execution
            
        Yields:
            Dict[str, Any]: Status updates and agent messages
            
        Example:
            async for update in agent_manager.run_workflow(
                prompt="Build a REST API",
                execution_type=ExecutionType.FULL,
            ):
                print(update)
        """
        try:
            # Create execution record
            execution = await self.create_execution(execution_type)
            
            # Initialize agents
            await self.initialize_agents()
            
            if not self.agents:
                raise ValueError("No agents initialized")
            
            # Update execution status
            await self.update_execution_status(ExecutionStatus.RUNNING)
            
            # Yield execution start event
            yield {
                "type": "execution_start",
                "execution_id": str(execution.id),
                "agents_count": len(self.agents),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Run workflow stages
            workflow_output = {}
            
            # Stage 1: Product Manager - Requirements Analysis
            yield from await self._run_product_manager_stage(prompt)
            
            # Stage 2: Architect - System Design
            yield from await self._run_architect_stage(prompt)
            
            # Stage 3: Engineer - Code Generation
            yield from await self._run_engineer_stage(prompt)
            
            # Stage 4: QA Engineer - Testing
            yield from await self._run_qa_engineer_stage(prompt)
            
            # Update project progress
            await self._update_project_progress(100.0)
            
            # Complete execution
            await self.update_execution_status(ExecutionStatus.COMPLETED)
            await self.set_execution_output(workflow_output)
            
            # Yield execution complete event
            yield {
                "type": "execution_complete",
                "execution_id": str(execution.id),
                "status": "completed",
                "output": workflow_output,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Update execution status to failed
            if self.execution:
                await self.update_execution_status(ExecutionStatus.FAILED)
                self.execution.fail(str(e))
                self.db.add(self.execution)
                await self.db.commit()
            
            # Yield error event
            yield {
                "type": "error",
                "error_code": "WORKFLOW_FAILED",
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    # ========================================================================
    # Workflow Stages
    # ========================================================================

    async def _run_product_manager_stage(
        self,
        prompt: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run Product Manager stage - Requirements Analysis.
        
        Args:
            prompt: Project requirements
            
        Yields:
            Dict[str, Any]: Stage updates
        """
        agent_role = AgentRole.PRODUCT_MANAGER.value
        
        if agent_role not in self.agents:
            logger.warning(f"Agent not available: {agent_role}")
            return
        
        agent = self.agents[agent_role]
        
        try:
            logger.info("Running Product Manager stage")
            
            # Yield stage start
            yield {
                "type": "stage_start",
                "stage": "requirements_analysis",
                "agent": agent_role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Generate requirements analysis
            analysis_prompt = f"""
            Analyze the following project requirements and create a detailed specification:
            
            {prompt}
            
            Provide:
            1. Project Overview
            2. Key Features
            3. User Stories
            4. Acceptance Criteria
            """
            
            # Get response from LLM
            response = await agent["llm_client"].generate(
                prompt=analysis_prompt,
                temperature=agent["llm_config"].get("temperature", 0.7),
                max_tokens=agent["llm_config"].get("max_tokens", 2000),
            )
            
            # Log response
            await self.add_execution_log(
                agent=agent_role,
                message=f"Generated requirements analysis",
                level="info",
            )
            
            # Yield agent message
            yield {
                "type": "agent_message",
                "agent": agent_role,
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Update progress
            await self._update_project_progress(25.0)
            
        except Exception as e:
            logger.error(f"Product Manager stage failed: {e}")
            await self.add_execution_log(
                agent=agent_role,
                message=f"Error: {str(e)}",
                level="error",
            )

    async def _run_architect_stage(
        self,
        prompt: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run Architect stage - System Design.
        
        Args:
            prompt: Project requirements
            
        Yields:
            Dict[str, Any]: Stage updates
        """
        agent_role = AgentRole.ARCHITECT.value
        
        if agent_role not in self.agents:
            logger.warning(f"Agent not available: {agent_role}")
            return
        
        agent = self.agents[agent_role]
        
        try:
            logger.info("Running Architect stage")
            
            # Yield stage start
            yield {
                "type": "stage_start",
                "stage": "system_design",
                "agent": agent_role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Generate system design
            design_prompt = f"""
            Design the system architecture for the following project:
            
            {prompt}
            
            Provide:
            1. System Architecture Diagram (ASCII)
            2. Component Descriptions
            3. Technology Stack
            4. Database Schema
            5. API Endpoints
            """
            
            # Get response from LLM
            response = await agent["llm_client"].generate(
                prompt=design_prompt,
                temperature=agent["llm_config"].get("temperature", 0.7),
                max_tokens=agent["llm_config"].get("max_tokens", 3000),
            )
            
            # Log response
            await self.add_execution_log(
                agent=agent_role,
                message=f"Generated system architecture design",
                level="info",
            )
            
            # Yield agent message
            yield {
                "type": "agent_message",
                "agent": agent_role,
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Update progress
            await self._update_project_progress(50.0)
            
        except Exception as e:
            logger.error(f"Architect stage failed: {e}")
            await self.add_execution_log(
                agent=agent_role,
                message=f"Error: {str(e)}",
                level="error",
            )

    async def _run_engineer_stage(
        self,
        prompt: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run Engineer stage - Code Generation.
        
        Args:
            prompt: Project requirements
            
        Yields:
            Dict[str, Any]: Stage updates
        """
        agent_role = AgentRole.ENGINEER.value
        
        if agent_role not in self.agents:
            logger.warning(f"Agent not available: {agent_role}")
            return
        
        agent = self.agents[agent_role]
        
        try:
            logger.info("Running Engineer stage")
            
            # Yield stage start
            yield {
                "type": "stage_start",
                "stage": "code_generation",
                "agent": agent_role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Generate code
            code_prompt = f"""
            Generate production-ready code for the following project:
            
            {prompt}
            
            Provide:
            1. Main application file
            2. API routes/endpoints
            3. Database models
            4. Configuration files
            5. Requirements/dependencies
            
            Use best practices and include proper error handling.
            """
            
            # Get response from LLM
            response = await agent["llm_client"].generate(
                prompt=code_prompt,
                temperature=agent["llm_config"].get("temperature", 0.5),
                max_tokens=agent["llm_config"].get("max_tokens", 4000),
            )
            
            # Log response
            await self.add_execution_log(
                agent=agent_role,
                message=f"Generated code implementation",
                level="info",
            )
            
            # Yield agent message
            yield {
                "type": "agent_message",
                "agent": agent_role,
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Update progress
            await self._update_project_progress(75.0)
            
        except Exception as e:
            logger.error(f"Engineer stage failed: {e}")
            await self.add_execution_log(
                agent=agent_role,
                message=f"Error: {str(e)}",
                level="error",
            )

    async def _run_qa_engineer_stage(
        self,
        prompt: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run QA Engineer stage - Testing.
        
        Args:
            prompt: Project requirements
            
        Yields:
            Dict[str, Any]: Stage updates
        """
        agent_role = AgentRole.QA_ENGINEER.value
        
        if agent_role not in self.agents:
            logger.warning(f"Agent not available: {agent_role}")
            return
        
        agent = self.agents[agent_role]
        
        try:
            logger.info("Running QA Engineer stage")
            
            # Yield stage start
            yield {
                "type": "stage_start",
                "stage": "testing",
                "agent": agent_role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Generate tests
            test_prompt = f"""
            Create comprehensive tests for the following project:
            
            {prompt}
            
            Provide:
            1. Unit tests
            2. Integration tests
            3. API endpoint tests
            4. Test coverage report
            5. Edge cases and error scenarios
            """
            
            # Get response from LLM
            response = await agent["llm_client"].generate(
                prompt=test_prompt,
                temperature=agent["llm_config"].get("temperature", 0.5),
                max_tokens=agent["llm_config"].get("max_tokens", 3000),
            )
            
            # Log response
            await self.add_execution_log(
                agent=agent_role,
                message=f"Generated test suite",
                level="info",
            )
            
            # Yield agent message
            yield {
                "type": "agent_message",
                "agent": agent_role,
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Update progress
            await self._update_project_progress(90.0)
            
        except Exception as e:
            logger.error(f"QA Engineer stage failed: {e}")
            await self.add_execution_log(
                agent=agent_role,
                message=f"Error: {str(e)}",
                level="error",
            )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _update_project_progress(self, progress: float) -> None:
        """
        Update project progress.
        
        Args:
            progress: Progress value (0-100)
        """
        try:
            self.project.update_progress(progress)
            self.db.add(self.project)
            await self.db.commit()
            
            logger.info(f"Updated project progress to: {progress}%")
            
        except Exception as e:
            logger.error(f"Failed to update project progress: {e}")

    async def cancel_execution(self) -> None:
        """Cancel the current execution."""
        if self.execution:
            self.execution.cancel()
            self.db.add(self.execution)
            await self.db.commit()
            logger.info("Execution cancelled")

    async def retry_execution(self) -> bool:
        """
        Retry the current execution.
        
        Returns:
            bool: True if retry is possible, False otherwise
        """
        if not self.execution:
            return False
        
        if not self.execution.can_retry():
            logger.warning("Maximum retries exceeded")
            return False
        
        self.execution.increment_retry()
        self.execution.status = ExecutionStatus.PENDING
        self.db.add(self.execution)
        await self.db.commit()
        
        logger.info(f"Retrying execution (attempt {self.execution.retry_count})")
        return True


# ============================================================================
# Factory Function
# ============================================================================

async def get_agent_manager(
    db: AsyncSession,
    project: Project,
    user_id: str,
) -> AgentManager:
    """
    Factory function to create an AgentManager instance.
    
    Args:
        db: Database session
        project: Project instance
        user_id: User ID
        
    Returns:
        AgentManager: Agent manager instance
    """
    return AgentManager(db, project, user_id)
