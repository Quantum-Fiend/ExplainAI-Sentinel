import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    Shield,
    Activity,
    Network,
    FileText,
    Users,
    Server,
    Menu,
    X,
    Bell,
    Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Activity },
    { name: 'Threats', href: '/threats', icon: Shield },
    { name: 'Knowledge Graph', href: '/knowledge-graph', icon: Network },
    { name: 'Policies', href: '/policies', icon: FileText },
    { name: 'Trust Scores', href: '/trust-scores', icon: Users },
    { name: 'Services', href: '/services', icon: Server },
];

interface LayoutProps {
    children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    return (
        <div className="min-h-screen bg-gray-950">
            {/* Mobile sidebar */}
            <div
                className={cn(
                    'fixed inset-0 z-50 bg-gray-900/80 lg:hidden',
                    sidebarOpen ? 'block' : 'hidden'
                )}
                onClick={() => setSidebarOpen(false)}
            />

            <div
                className={cn(
                    'fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform lg:translate-x-0',
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                )}
            >
                <div className="flex h-16 items-center justify-between px-6 border-b border-gray-800">
                    <div className="flex items-center space-x-3">
                        <Shield className="h-8 w-8 text-primary-500" />
                        <span className="text-xl font-bold text-white">ExplainAI</span>
                    </div>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden text-gray-400 hover:text-white"
                    >
                        <X className="h-6 w-6" />
                    </button>
                </div>

                <nav className="mt-6 px-3">
                    {navigation.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                className={cn(
                                    'flex items-center space-x-3 px-3 py-2.5 rounded-lg mb-1 transition-colors',
                                    isActive
                                        ? 'bg-primary-600 text-white'
                                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                )}
                            >
                                <item.icon className="h-5 w-5" />
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
                    <div className="text-xs text-gray-500 text-center">
                        <p>ExplainAI-Sentinel v1.0.0</p>
                        <p className="mt-1">Production Ready</p>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="lg:pl-64">
                {/* Top bar */}
                <div className="sticky top-0 z-40 flex h-16 items-center justify-between bg-gray-900 border-b border-gray-800 px-4 sm:px-6">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden text-gray-400 hover:text-white"
                    >
                        <Menu className="h-6 w-6" />
                    </button>

                    <div className="flex-1" />

                    <div className="flex items-center space-x-4">
                        <button className="relative text-gray-400 hover:text-white">
                            <Bell className="h-6 w-6" />
                            <span className="absolute -top-1 -right-1 h-4 w-4 bg-danger-500 rounded-full text-xs text-white flex items-center justify-center">
                                3
                            </span>
                        </button>

                        <button className="text-gray-400 hover:text-white">
                            <Settings className="h-6 w-6" />
                        </button>

                        <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-medium">
                            A
                        </div>
                    </div>
                </div>

                {/* Page content */}
                <main className="p-6">{children}</main>
            </div>
        </div>
    );
}
