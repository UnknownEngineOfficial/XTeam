import React from 'react';
import { Link } from 'react-router-dom';
import { Plus, FolderOpen, Settings, User } from 'lucide-react';
import Button from '../components/common/Button';

const Dashboard: React.FC = () => {
  // Mock data - später durch echte API-Daten ersetzen
  const projects = [
    {
      id: '1',
      name: 'E-Commerce Plattform',
      description: 'Eine vollständige E-Commerce-Lösung mit KI-gestützter Produktempfehlung',
      status: 'active',
      progress: 75,
      lastModified: '2024-01-15',
    },
    {
      id: '2',
      name: 'Task Management App',
      description: 'Moderne Aufgabenverwaltung mit Team-Kollaboration',
      status: 'draft',
      progress: 20,
      lastModified: '2024-01-10',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">XTeam</h1>
              <span className="ml-2 text-sm text-gray-500">Multi-Agent-Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/settings">
                <Button variant="ghost" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Einstellungen
                </Button>
              </Link>
              <Button variant="ghost" size="sm">
                <User className="w-4 h-4 mr-2" />
                Profil
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Willkommen bei XTeam
          </h2>
          <p className="text-lg text-gray-600">
            Erstelle und verwalte KI-gestützte Softwareprojekte mit unserem Multi-Agent-System.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-4">
            <Link to="/project/new">
              <Button size="lg" className="flex items-center">
                <Plus className="w-5 h-5 mr-2" />
                Neues Projekt
              </Button>
            </Link>
            <Button variant="outline" size="lg">
              <FolderOpen className="w-5 h-5 mr-2" />
              Projekt importieren
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Meine Projekte
          </h3>

          {projects.length === 0 ? (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Noch keine Projekte
              </h4>
              <p className="text-gray-600 mb-4">
                Erstelle dein erstes KI-gestütztes Softwareprojekt.
              </p>
              <Link to="/project/new">
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Projekt erstellen
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <Link
                  key={project.id}
                  to={`/project/${project.id}`}
                  className="block"
                >
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">
                        {project.name}
                      </h4>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                        {project.status === 'active' ? 'Aktiv' :
                         project.status === 'draft' ? 'Entwurf' : 'Abgeschlossen'}
                      </span>
                    </div>

                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {project.description}
                    </p>

                    <div className="mb-4">
                      <div className="flex justify-between text-sm text-gray-600 mb-1">
                        <span>Fortschritt</span>
                        <span>{project.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${project.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="text-xs text-gray-500">
                      Zuletzt bearbeitet: {new Date(project.lastModified).toLocaleDateString('de-DE')}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FolderOpen className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Projekte</p>
                <p className="text-2xl font-bold text-gray-900">{projects.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <Plus className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Aktive Projekte</p>
                <p className="text-2xl font-bold text-gray-900">
                  {projects.filter(p => p.status === 'active').length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Settings className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">KI-Agenten</p>
                <p className="text-2xl font-bold text-gray-900">4</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;