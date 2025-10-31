import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  Settings,
  Code,
  Terminal,
  Eye,
  MessageSquare
} from 'lucide-react';
import Button from '../components/common/Button';
import ChatInterface from '../components/chat/ChatInterface';
import CodeEditor from '../components/editor/CodeEditor';
import FileTree from '../components/editor/FileTree';
import TerminalComponent from '../components/editor/Terminal';
import LivePreview from '../components/preview/LivePreview';

type TabType = 'chat' | 'editor' | 'preview' | 'terminal';

const ProjectView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [project, setProject] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('// Welcome to XTeam Code Editor\n// Start coding your project here!');

  // Mock project data - später durch echte API ersetzen
  useEffect(() => {
    const mockProject = {
      id,
      name: 'E-Commerce Plattform',
      description: 'Eine vollständige E-Commerce-Lösung mit KI-gestützter Produktempfehlung',
      status: 'active',
      progress: 75,
      requirements: 'Erstelle eine moderne E-Commerce-Plattform mit Produktkatalog, Warenkorb und Zahlungssystem.',
      createdAt: '2024-01-15',
      workspace: {
        files: [
          { name: 'package.json', type: 'file', path: '/package.json' },
          { name: 'src', type: 'folder', path: '/src', children: [
            { name: 'App.tsx', type: 'file', path: '/src/App.tsx' },
            { name: 'index.tsx', type: 'file', path: '/src/index.tsx' },
          ]},
        ]
      }
    };
    setProject(mockProject);
  }, [id]);

  const handleStartExecution = () => {
    setIsRunning(true);
    // Hier würde die WebSocket-Verbindung gestartet werden
  };

  const handleStopExecution = () => {
    setIsRunning(false);
    // Hier würde die Ausführung gestoppt werden
  };

  const tabs = [
    { id: 'chat' as TabType, label: 'Chat', icon: MessageSquare },
    { id: 'editor' as TabType, label: 'Editor', icon: Code },
    { id: 'preview' as TabType, label: 'Vorschau', icon: Eye },
    { id: 'terminal' as TabType, label: 'Terminal', icon: Terminal },
  ];

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-400 hover:text-gray-600"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{project.name}</h1>
                <p className="text-sm text-gray-600">{project.description}</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-sm text-gray-600">Fortschritt</div>
                <div className="text-lg font-semibold text-gray-900">{project.progress}%</div>
              </div>

              <div className="w-24 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${project.progress}%` }}
                ></div>
              </div>

              <Button
                variant="ghost"
                size="sm"
              >
                <Settings className="w-4 h-4" />
              </Button>

              {!isRunning ? (
                <Button
                  onClick={handleStartExecution}
                  className="flex items-center"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStopExecution}
                  >
                    <Pause className="w-4 h-4 mr-2" />
                    Pause
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStopExecution}
                  >
                    <Square className="w-4 h-4 mr-2" />
                    Stop
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Sidebar - File Tree */}
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-900">Projekt-Dateien</h3>
          </div>
          <div className="flex-1 overflow-y-auto">
            <FileTree
              files={project.workspace.files}
              onFileSelect={(file) => setSelectedFile(file.path)}
              onFileCreate={(path, type) => console.log('Create file:', path, type)}
              onFileDelete={(path) => console.log('Delete file:', path)}
              selectedFile={selectedFile}
            />
          </div>
        </div>

        {/* Main Panel */}
        <div className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="bg-white border-b border-gray-200">
            <div className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'chat' && <ChatInterface />}
            {activeTab === 'editor' && (
              <CodeEditor
                value={fileContent}
                onChange={setFileContent}
                language="typescript"
                theme="light"
                readOnly={false}
              />
            )}
            {activeTab === 'preview' && (
              <LivePreview
                html={'<h1>Hello, World!</h1>'}
                css={'body { font-family: Arial, sans-serif; }'}
                js={'console.log("Hello from XTeam!");'}
              />
            )}
            {activeTab === 'terminal' && (
              <TerminalComponent
                onCommand={async (command) => {
                  // Mock terminal command execution
                  return `Executed: ${command}\nOutput: Command completed successfully`;
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectView;