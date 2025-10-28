"""
File Handler

This module provides file system abstraction for managing project workspaces
and generated files.
"""

import os
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from pathlib import Path
import shutil
import json
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# File Handler Class
# ============================================================================

class FileHandler:
    """
    File system abstraction for managing project workspaces.
    
    Provides methods for creating, reading, writing, and managing files
    within project workspaces.
    """

    def __init__(self, workspace_root: str = settings.metagpt_workspace):
        """
        Initialize file handler.
        
        Args:
            workspace_root: Root directory for all workspaces
        """
        self.workspace_root = workspace_root
        logger.info(f"Initialized FileHandler with root: {workspace_root}")

    # ========================================================================
    # Workspace Management
    # ========================================================================

    def get_workspace_path(self, project_id: str) -> str:
        """
        Get the workspace path for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            str: Workspace path
        """
        return os.path.join(self.workspace_root, str(project_id))

    def create_workspace(self, project_id: str) -> str:
        """
        Create a workspace directory for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            str: Created workspace path
            
        Raises:
            OSError: If workspace creation fails
        """
        workspace_path = self.get_workspace_path(project_id)
        
        try:
            os.makedirs(workspace_path, exist_ok=True)
            logger.info(f"Created workspace: {workspace_path}")
            
            # Create standard subdirectories
            subdirs = ["src", "tests", "docs", "config", "output"]
            for subdir in subdirs:
                subdir_path = os.path.join(workspace_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
            
            return workspace_path
            
        except OSError as e:
            logger.error(f"Failed to create workspace: {e}")
            raise

    def delete_workspace(self, project_id: str) -> bool:
        """
        Delete a workspace directory.
        
        Args:
            project_id: Project ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        workspace_path = self.get_workspace_path(project_id)
        
        if not os.path.exists(workspace_path):
            logger.warning(f"Workspace not found: {workspace_path}")
            return False
        
        try:
            shutil.rmtree(workspace_path)
            logger.info(f"Deleted workspace: {workspace_path}")
            return True
            
        except OSError as e:
            logger.error(f"Failed to delete workspace: {e}")
            raise

    def workspace_exists(self, project_id: str) -> bool:
        """
        Check if a workspace exists.
        
        Args:
            project_id: Project ID
            
        Returns:
            bool: True if workspace exists
        """
        workspace_path = self.get_workspace_path(project_id)
        return os.path.isdir(workspace_path)

    def get_workspace_size(self, project_id: str) -> int:
        """
        Get the total size of a workspace in bytes.
        
        Args:
            project_id: Project ID
            
        Returns:
            int: Total size in bytes
        """
        workspace_path = self.get_workspace_path(project_id)
        
        if not os.path.exists(workspace_path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(workspace_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        
        return total_size

    # ========================================================================
    # File Operations
    # ========================================================================

    def write_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        create_dirs: bool = True,
    ) -> str:
        """
        Write content to a file in the workspace.
        
        Args:
            project_id: Project ID
            file_path: Relative file path within workspace
            content: File content
            create_dirs: Whether to create parent directories
            
        Returns:
            str: Full file path
            
        Raises:
            ValueError: If file path is invalid
            OSError: If file write fails
        """
        # Validate file path
        if file_path.startswith("/") or ".." in file_path:
            raise ValueError(f"Invalid file path: {file_path}")
        
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, file_path)
        
        # Ensure path is within workspace
        full_path = os.path.abspath(full_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not full_path.startswith(workspace_path):
            raise ValueError(f"File path outside workspace: {file_path}")
        
        try:
            # Create parent directories if needed
            if create_dirs:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Wrote file: {full_path}")
            return full_path
            
        except OSError as e:
            logger.error(f"Failed to write file: {e}")
            raise

    def read_file(
        self,
        project_id: str,
        file_path: str,
    ) -> str:
        """
        Read content from a file in the workspace.
        
        Args:
            project_id: Project ID
            file_path: Relative file path within workspace
            
        Returns:
            str: File content
            
        Raises:
            ValueError: If file path is invalid
            FileNotFoundError: If file not found
        """
        # Validate file path
        if file_path.startswith("/") or ".." in file_path:
            raise ValueError(f"Invalid file path: {file_path}")
        
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, file_path)
        
        # Ensure path is within workspace
        full_path = os.path.abspath(full_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not full_path.startswith(workspace_path):
            raise ValueError(f"File path outside workspace: {file_path}")
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            logger.info(f"Read file: {full_path}")
            return content
            
        except OSError as e:
            logger.error(f"Failed to read file: {e}")
            raise

    def append_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
    ) -> str:
        """
        Append content to a file in the workspace.
        
        Args:
            project_id: Project ID
            file_path: Relative file path within workspace
            content: Content to append
            
        Returns:
            str: Full file path
            
        Raises:
            ValueError: If file path is invalid
            OSError: If file operation fails
        """
        # Validate file path
        if file_path.startswith("/") or ".." in file_path:
            raise ValueError(f"Invalid file path: {file_path}")
        
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, file_path)
        
        # Ensure path is within workspace
        full_path = os.path.abspath(full_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not full_path.startswith(workspace_path):
            raise ValueError(f"File path outside workspace: {file_path}")
        
        try:
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Appended to file: {full_path}")
            return full_path
            
        except OSError as e:
            logger.error(f"Failed to append to file: {e}")
            raise

    def delete_file(
        self,
        project_id: str,
        file_path: str,
    ) -> bool:
        """
        Delete a file from the workspace.
        
        Args:
            project_id: Project ID
            file_path: Relative file path within workspace
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            ValueError: If file path is invalid
        """
        # Validate file path
        if file_path.startswith("/") or ".." in file_path:
            raise ValueError(f"Invalid file path: {file_path}")
        
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, file_path)
        
        # Ensure path is within workspace
        full_path = os.path.abspath(full_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not full_path.startswith(workspace_path):
            raise ValueError(f"File path outside workspace: {file_path}")
        
        if not os.path.exists(full_path):
            logger.warning(f"File not found: {full_path}")
            return False
        
        try:
            os.remove(full_path)
            logger.info(f"Deleted file: {full_path}")
            return True
            
        except OSError as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    def file_exists(
        self,
        project_id: str,
        file_path: str,
    ) -> bool:
        """
        Check if a file exists in the workspace.
        
        Args:
            project_id: Project ID
            file_path: Relative file path within workspace
            
        Returns:
            bool: True if file exists
        """
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, file_path)
        return os.path.isfile(full_path)

    # ========================================================================
    # Directory Operations
    # ========================================================================

    def list_files(
        self,
        project_id: str,
        directory: str = "",
        recursive: bool = False,
    ) -> List[str]:
        """
        List files in a directory within the workspace.
        
        Args:
            project_id: Project ID
            directory: Relative directory path (empty for root)
            recursive: Whether to list recursively
            
        Returns:
            List[str]: List of relative file paths
            
        Raises:
            ValueError: If directory path is invalid
        """
        # Validate directory path
        if directory.startswith("/") or ".." in directory:
            raise ValueError(f"Invalid directory path: {directory}")
        
        workspace_path = self.get_workspace_path(project_id)
        dir_path = os.path.join(workspace_path, directory) if directory else workspace_path
        
        # Ensure path is within workspace
        dir_path = os.path.abspath(dir_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not dir_path.startswith(workspace_path):
            raise ValueError(f"Directory path outside workspace: {directory}")
        
        if not os.path.isdir(dir_path):
            return []
        
        files = []
        
        try:
            if recursive:
                for dirpath, dirnames, filenames in os.walk(dir_path):
                    for filename in filenames:
                        full_path = os.path.join(dirpath, filename)
                        rel_path = os.path.relpath(full_path, workspace_path)
                        files.append(rel_path)
            else:
                for item in os.listdir(dir_path):
                    full_path = os.path.join(dir_path, item)
                    if os.path.isfile(full_path):
                        rel_path = os.path.relpath(full_path, workspace_path)
                        files.append(rel_path)
            
            return sorted(files)
            
        except OSError as e:
            logger.error(f"Failed to list files: {e}")
            raise

    def list_directories(
        self,
        project_id: str,
        directory: str = "",
    ) -> List[str]:
        """
        List directories in a directory within the workspace.
        
        Args:
            project_id: Project ID
            directory: Relative directory path (empty for root)
            
        Returns:
            List[str]: List of relative directory paths
            
        Raises:
            ValueError: If directory path is invalid
        """
        # Validate directory path
        if directory.startswith("/") or ".." in directory:
            raise ValueError(f"Invalid directory path: {directory}")
        
        workspace_path = self.get_workspace_path(project_id)
        dir_path = os.path.join(workspace_path, directory) if directory else workspace_path
        
        # Ensure path is within workspace
        dir_path = os.path.abspath(dir_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not dir_path.startswith(workspace_path):
            raise ValueError(f"Directory path outside workspace: {directory}")
        
        if not os.path.isdir(dir_path):
            return []
        
        directories = []
        
        try:
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                if os.path.isdir(full_path):
                    rel_path = os.path.relpath(full_path, workspace_path)
                    directories.append(rel_path)
            
            return sorted(directories)
            
        except OSError as e:
            logger.error(f"Failed to list directories: {e}")
            raise

    def create_directory(
        self,
        project_id: str,
        directory: str,
    ) -> str:
        """
        Create a directory in the workspace.
        
        Args:
            project_id: Project ID
            directory: Relative directory path
            
        Returns:
            str: Full directory path
            
        Raises:
            ValueError: If directory path is invalid
            OSError: If directory creation fails
        """
        # Validate directory path
        if directory.startswith("/") or ".." in directory:
            raise ValueError(f"Invalid directory path: {directory}")
        
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, directory)
        
        # Ensure path is within workspace
        full_path = os.path.abspath(full_path)
        workspace_path = os.path.abspath(workspace_path)
        
        if not full_path.startswith(workspace_path):
            raise ValueError(f"Directory path outside workspace: {directory}")
        
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            return full_path
            
        except OSError as e:
            logger.error(f"Failed to create directory: {e}")
            raise

    # ========================================================================
    # File Tree Operations
    # ========================================================================

    def get_file_tree(
        self,
        project_id: str,
        directory: str = "",
        max_depth: int = 10,
    ) -> Dict[str, Any]:
        """
        Get a tree structure of files and directories.
        
        Args:
            project_id: Project ID
            directory: Relative directory path (empty for root)
            max_depth: Maximum depth to traverse
            
        Returns:
            Dict[str, Any]: Tree structure
        """
        workspace_path = self.get_workspace_path(project_id)
        dir_path = os.path.join(workspace_path, directory) if directory else workspace_path
        
        def build_tree(path: str, depth: int = 0) -> Dict[str, Any]:
            if depth > max_depth:
                return {}
            
            tree = {
                "name": os.path.basename(path) or "root",
                "type": "directory",
                "path": os.path.relpath(path, workspace_path),
                "children": [],
            }
            
            try:
                for item in sorted(os.listdir(path)):
                    item_path = os.path.join(path, item)
                    
                    if os.path.isdir(item_path):
                        tree["children"].append(build_tree(item_path, depth + 1))
                    else:
                        tree["children"].append({
                            "name": item,
                            "type": "file",
                            "path": os.path.relpath(item_path, workspace_path),
                            "size": os.path.getsize(item_path),
                        })
            except OSError:
                pass
            
            return tree
        
        return build_tree(dir_path)

    # ========================================================================
    # JSON Operations
    # ========================================================================

    def write_json(
        self,
        project_id: str,
        file_path: str,
        data: Dict[str, Any],
        pretty: bool = True,
    ) -> str:
        """
        Write JSON data to a file.
        
        Args:
            project_id: Project ID
            file_path: Relative file path
            data: Data to write
            pretty: Whether to pretty-print JSON
            
        Returns:
            str: Full file path
        """
        content = json.dumps(data, indent=2 if pretty else None)
        return self.write_file(project_id, file_path, content)

    def read_json(
        self,
        project_id: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Read JSON data from a file.
        
        Args:
            project_id: Project ID
            file_path: Relative file path
            
        Returns:
            Dict[str, Any]: Parsed JSON data
        """
        content = self.read_file(project_id, file_path)
        return json.loads(content)

    # ========================================================================
    # File Metadata
    # ========================================================================

    def get_file_info(
        self,
        project_id: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Get file metadata.
        
        Args:
            project_id: Project ID
            file_path: Relative file path
            
        Returns:
            Dict[str, Any]: File metadata
            
        Raises:
            FileNotFoundError: If file not found
        """
        workspace_path = self.get_workspace_path(project_id)
        full_path = os.path.join(workspace_path, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        
        stat = os.stat(full_path)
        
        return {
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "is_file": os.path.isfile(full_path),
            "is_directory": os.path.isdir(full_path),
        }

    # ========================================================================
    # Backup and Restore
    # ========================================================================

    def backup_workspace(
        self,
        project_id: str,
        backup_path: str,
    ) -> str:
        """
        Create a backup of the workspace.
        
        Args:
            project_id: Project ID
            backup_path: Path to save backup
            
        Returns:
            str: Backup file path
        """
        workspace_path = self.get_workspace_path(project_id)
        
        if not os.path.exists(workspace_path):
            raise FileNotFoundError(f"Workspace not found: {workspace_path}")
        
        try:
            backup_file = shutil.make_archive(
                backup_path,
                "zip",
                workspace_path,
            )
            logger.info(f"Created backup: {backup_file}")
            return backup_file
            
        except OSError as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_workspace(
        self,
        project_id: str,
        backup_path: str,
    ) -> str:
        """
        Restore a workspace from backup.
        
        Args:
            project_id: Project ID
            backup_path: Path to backup file
            
        Returns:
            str: Restored workspace path
        """
        workspace_path = self.get_workspace_path(project_id)
        
        try:
            # Remove existing workspace
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
            
            # Extract backup
            shutil.unpack_archive(backup_path, workspace_path)
            logger.info(f"Restored workspace from: {backup_path}")
            return workspace_path
            
        except OSError as e:
            logger.error(f"Failed to restore workspace: {e}")
            raise


# ============================================================================
# Global File Handler Instance
# ============================================================================

_file_handler = FileHandler()


# ============================================================================
# Factory Function
# ============================================================================

def get_file_handler(workspace_root: Optional[str] = None) -> FileHandler:
    """
    Get a file handler instance.
    
    Args:
        workspace_root: Optional custom workspace root
        
    Returns:
        FileHandler: File handler instance
    """
    if workspace_root:
        return FileHandler(workspace_root)
    return _file_handler
