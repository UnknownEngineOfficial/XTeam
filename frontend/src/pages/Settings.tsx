import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, Key, Bell, Palette, Database } from 'lucide-react';
import Button from '../components/common/Button';
import toast from 'react-hot-toast';

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'profile' | 'api' | 'notifications' | 'appearance' | 'data'>('profile');
  const [loading, setLoading] = useState(false);

  const [profileData, setProfileData] = useState({
    username: 'johndoe',
    email: 'john@example.com',
    fullName: 'John Doe',
    bio: 'Softwareentwickler und KI-Enthusiast',
  });

  const [apiData, setApiData] = useState({
    openaiKey: '',
    anthropicKey: '',
    groqKey: '',
  });

  const handleProfileSave = async () => {
    setLoading(true);
    try {
      // Mock save - später durch echte API ersetzen
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('Profil gespeichert!');
    } catch (error) {
      toast.error('Fehler beim Speichern');
    } finally {
      setLoading(false);
    }
  };

  const handleApiSave = async () => {
    setLoading(true);
    try {
      // Mock save - später durch echte API ersetzen
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('API-Schlüssel gespeichert!');
    } catch (error) {
      toast.error('Fehler beim Speichern');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile' as const, label: 'Profil', icon: User },
    { id: 'api' as const, label: 'API-Schlüssel', icon: Key },
    { id: 'notifications' as const, label: 'Benachrichtigungen', icon: Bell },
    { id: 'appearance' as const, label: 'Erscheinungsbild', icon: Palette },
    { id: 'data' as const, label: 'Daten & Datenschutz', icon: Database },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-400 hover:text-gray-600"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Einstellungen</h1>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex space-x-8">
          {/* Sidebar */}
          <div className="w-64">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="bg-white shadow-sm rounded-lg">
              {/* Profile Settings */}
              {activeTab === 'profile' && (
                <div className="p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-6">Profil-Einstellungen</h2>

                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Benutzername
                      </label>
                      <input
                        type="text"
                        value={profileData.username}
                        onChange={(e) => setProfileData(prev => ({ ...prev, username: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        E-Mail-Adresse
                      </label>
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Vollständiger Name
                      </label>
                      <input
                        type="text"
                        value={profileData.fullName}
                        onChange={(e) => setProfileData(prev => ({ ...prev, fullName: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Bio
                      </label>
                      <textarea
                        rows={3}
                        value={profileData.bio}
                        onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Erzähl etwas über dich..."
                      />
                    </div>

                    <div className="flex justify-end">
                      <Button onClick={handleProfileSave} loading={loading}>
                        Speichern
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* API Keys Settings */}
              {activeTab === 'api' && (
                <div className="p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-6">API-Schlüssel</h2>

                  <div className="space-y-6">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <div className="flex">
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-yellow-800">
                            Sicherheitshinweis
                          </h3>
                          <div className="mt-2 text-sm text-yellow-700">
                            <p>
                              API-Schlüssel werden verschlüsselt gespeichert. Teile diese Schlüssel niemals mit anderen.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        OpenAI API-Schlüssel
                      </label>
                      <input
                        type="password"
                        value={apiData.openaiKey}
                        onChange={(e) => setApiData(prev => ({ ...prev, openaiKey: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="sk-..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Anthropic API-Schlüssel
                      </label>
                      <input
                        type="password"
                        value={apiData.anthropicKey}
                        onChange={(e) => setApiData(prev => ({ ...prev, anthropicKey: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="sk-ant-..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Groq API-Schlüssel
                      </label>
                      <input
                        type="password"
                        value={apiData.groqKey}
                        onChange={(e) => setApiData(prev => ({ ...prev, groqKey: e.target.value }))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="gsk_..."
                      />
                    </div>

                    <div className="flex justify-end">
                      <Button onClick={handleApiSave} loading={loading}>
                        Speichern
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Notifications Settings */}
              {activeTab === 'notifications' && (
                <div className="p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-6">Benachrichtigungen</h2>
                  <p className="text-gray-600">Benachrichtigungseinstellungen werden bald verfügbar sein.</p>
                </div>
              )}

              {/* Appearance Settings */}
              {activeTab === 'appearance' && (
                <div className="p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-6">Erscheinungsbild</h2>
                  <p className="text-gray-600">Erscheinungsbildeinstellungen werden bald verfügbar sein.</p>
                </div>
              )}

              {/* Data & Privacy Settings */}
              {activeTab === 'data' && (
                <div className="p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-6">Daten & Datenschutz</h2>
                  <p className="text-gray-600">Daten- und Datenschutzeinstellungen werden bald verfügbar sein.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;