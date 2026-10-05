import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  BookOpen,
  FileText,
  AlertTriangle,
  Bookmark,
  Settings,
  Menu,
} from 'lucide-react';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Ask HealthCompass', href: '/ask', icon: MessageSquare },
  { name: 'Guidance Library', href: '/guidance', icon: BookOpen },
  { name: 'Updates & Policies', href: '/updates', icon: FileText },
  { name: 'Alert Center', href: '/alerts', icon: AlertTriangle },
  { name: 'Saved Guidance', href: '/saved', icon: Bookmark },
];

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md"
      >
        <Menu className="h-6 w-6" />
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <LayoutDashboard className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">HealthCompass</h1>
                <p className="text-xs text-gray-500">Public Health Guidance</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User profile */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-gray-600">SM</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Sarah Miller</p>
                <p className="text-xs text-gray-500">Field Worker</p>
              </div>
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <Settings className="h-5 w-5 text-gray-500" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className={`flex-1 transition-all duration-300 ease-in-out ${sidebarOpen ? 'lg:ml-64' : ''}`}>
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default Layout;
