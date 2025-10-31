import React, { useState, useEffect } from 'react';
import {
  Folder,
  FolderOpen,
  File,
  FileText,
  FileCode,
  Image,
  Settings,
  ChevronRight,
  ChevronDown,
  Plus,
  MoreVertical,
} from 'lucide-react';
import Button from '../common/Button';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  path: string;
  children?: FileNode[];
  isOpen?: boolean;
}

interface FileTreeProps {
  files: FileNode[];
  onFileSelect: (file: FileNode) => void;
  onFileCreate: (path: string, type: 'file' | 'folder') => void;
  onFileDelete: (path: string) => void;
  selectedFile?: string;
  className?: string;
}

const FileTree: React.FC<FileTreeProps> = ({
  files,
  onFileSelect,
  onFileCreate,
  onFileDelete,
  selectedFile,
  className = '',
}) => {
  const [fileTree, setFileTree] = useState<FileNode[]>(files);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    file: FileNode;
  } | null>(null);

  useEffect(() => {
    setFileTree(files);
  }, [files]);

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();

    switch (ext) {
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx':
        return <FileCode className="w-4 h-4 text-yellow-600" />;
      case 'json':
        return <Settings className="w-4 h-4 text-green-600" />;
      case 'md':
        return <FileText className="w-4 h-4 text-blue-600" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
      case 'svg':
        return <Image className="w-4 h-4 text-purple-600" />;
      default:
        return <File className="w-4 h-4 text-gray-600" />;
    }
  };

  const toggleFolder = (node: FileNode) => {
    const updateTree = (nodes: FileNode[]): FileNode[] => {
      return nodes.map(n => {
        if (n.path === node.path) {
          return { ...n, isOpen: !n.isOpen };
        }
        if (n.children) {
          return { ...n, children: updateTree(n.children) };
        }
        return n;
      });
    };

    setFileTree(updateTree(fileTree));
  };

  const handleContextMenu = (e: React.MouseEvent, file: FileNode) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      file,
    });
  };

  const handleCreateFile = () => {
    if (!contextMenu) return;
    const fileName = prompt('Enter file name:');
    if (fileName) {
      const path = contextMenu.file.type === 'folder'
        ? `${contextMenu.file.path}/${fileName}`
        : `${contextMenu.file.path.split('/').slice(0, -1).join('/')}/${fileName}`;
      onFileCreate(path, 'file');
    }
    setContextMenu(null);
  };

  const handleCreateFolder = () => {
    if (!contextMenu) return;
    const folderName = prompt('Enter folder name:');
    if (folderName) {
      const path = contextMenu.file.type === 'folder'
        ? `${contextMenu.file.path}/${folderName}`
        : `${contextMenu.file.path.split('/').slice(0, -1).join('/')}/${folderName}`;
      onFileCreate(path, 'folder');
    }
    setContextMenu(null);
  };

  const handleDelete = () => {
    if (!contextMenu) return;
    if (confirm(`Are you sure you want to delete ${contextMenu.file.name}?`)) {
      onFileDelete(contextMenu.file.path);
    }
    setContextMenu(null);
  };

  const renderNode = (node: FileNode, level: number = 0) => {
    const isSelected = selectedFile === node.path;
    const paddingLeft = level * 20 + 8;

    return (
      <div key={node.path}>
        <div
          className={`flex items-center py-1 px-2 hover:bg-gray-100 cursor-pointer group ${
            isSelected ? 'bg-blue-100 text-blue-900' : 'text-gray-700'
          }`}
          style={{ paddingLeft }}
          onClick={() => {
            if (node.type === 'folder') {
              toggleFolder(node);
            } else {
              onFileSelect(node);
            }
          }}
          onContextMenu={(e) => handleContextMenu(e, node)}
        >
          {node.type === 'folder' ? (
            <>
              {node.isOpen ? (
                <ChevronDown className="w-4 h-4 mr-1 text-gray-500" />
              ) : (
                <ChevronRight className="w-4 h-4 mr-1 text-gray-500" />
              )}
              {node.isOpen ? (
                <FolderOpen className="w-4 h-4 mr-2 text-blue-600" />
              ) : (
                <Folder className="w-4 h-4 mr-2 text-blue-600" />
              )}
            </>
          ) : (
            <div className="w-4 h-4 mr-1" />
          )}

          {node.type === 'file' && (
            <div className="mr-2">
              {getFileIcon(node.name)}
            </div>
          )}

          <span className="text-sm truncate flex-1">{node.name}</span>

          <div className="opacity-0 group-hover:opacity-100 ml-2">
            <MoreVertical className="w-4 h-4 text-gray-400" />
          </div>
        </div>

        {node.type === 'folder' && node.isOpen && node.children && (
          <div>
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`h-full bg-white border-r border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-900">Project Files</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFileCreate('', 'folder')}
          className="p-1"
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      {/* File Tree */}
      <div className="overflow-y-auto h-full pb-4">
        {fileTree.map(node => renderNode(node))}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setContextMenu(null)}
          />
          <div
            className="fixed z-20 bg-white border border-gray-200 rounded-md shadow-lg py-1 min-w-48"
            style={{ left: contextMenu.x, top: contextMenu.y }}
          >
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100"
              onClick={handleCreateFile}
            >
              New File
            </button>
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100"
              onClick={handleCreateFolder}
            >
              New Folder
            </button>
            <hr className="my-1" />
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 text-red-600"
              onClick={handleDelete}
            >
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default FileTree;
