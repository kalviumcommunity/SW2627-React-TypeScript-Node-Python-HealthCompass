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
  X,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { getUnreadCount } from '../api/client';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Ask HealthCompass', href: '/ask', icon: MessageSquare },
  { name: 'Guidance Library', href: '/guidance', icon: BookOpen },
  { name: 'Updates', href: '/updates', icon: FileText },
  { name: 'Alert Center', href: '/alerts', icon: AlertTriangle },
  { name: 'Saved Guidance', href: '/saved', icon: Bookmark },
];

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const location = useLocation();

  useEffect(() => {
    // Load unread count
    getUnreadCount()
      .then((data) => setUnreadCount(data.count))
      .catch(console.error);
  }, [location]); // Reload when location changes to update after reading

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-sm"
      >
        {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
        />
      )}

      {/* Sidebar - fixed on both desktop and mobile */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[240px] bg-white border-r border-gray-200 transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
                <LayoutDashboard className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold text-gray-900">HealthCompass</h1>
                <p className="text-xs text-gray-500">Field Operations</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const showBadge = item.name === 'Updates' && unreadCount > 0;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-teal-50 text-teal-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="h-4 w-4" />
                    {item.name}
                  </div>
                  {showBadge && (
                    <span className="bg-teal-600 text-white text-xs px-2 py-0.5 rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User profile */}
          <div className="p-3 border-t border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-xs font-medium text-gray-600">SJ</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">Sarah Jenkins</p>
                <p className="text-xs text-gray-500 truncate">Field Medical Officer</p>
              </div>
              <button className="p-1.5 hover:bg-gray-100 rounded-md">
                <Settings className="h-4 w-4 text-gray-500" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content - margin-left on desktop only */}
      <main className="lg:ml-[240px] min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
