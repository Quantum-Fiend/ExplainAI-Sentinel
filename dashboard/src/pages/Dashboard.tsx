import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Shield, AlertTriangle, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { mockData, aiApi, policyApi, runtimeApi } from '@/api/client';
import { cn } from '@/lib/utils';

export default function Dashboard() {
    const { data: metrics } = useQuery({
        queryKey: ['metrics'],
        queryFn: () => mockData.metrics(),
        refetchInterval: 5000,
    });

    const { data: alerts } = useQuery({
        queryKey: ['alerts'],
        queryFn: () => mockData.alerts(),
    });

    const stats = [
        {
            name: 'Active Threats',
            value: '12',
            change: '+2',
            changeType: 'increase',
            icon: Shield,
            color: 'danger',
        },
        {
            name: 'Anomalies Detected',
            value: '47',
            change: '+8',
            changeType: 'increase',
            icon: AlertTriangle,
            color: 'warning',
        },
        {
            name: 'Trust Score Avg',
            value: '0.85',
            change: '+0.05',
            changeType: 'increase',
            icon: Activity,
            color: 'success',
        },
        {
            name: 'Active Services',
            value: '24',
            change: '0',
            changeType: 'neutral',
            icon: TrendingUp,
            color: 'primary',
        },
    ];

    const metricsHistory = Array.from({ length: 20 }, (_, i) => ({
        time: `${i}m`,
        cpu: 40 + Math.random() * 30,
        memory: 50 + Math.random() * 25,
        requests: 400 + Math.random() * 200,
    }));

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Security Dashboard</h1>
                <p className="mt-2 text-gray-400">
                    Real-time monitoring and threat detection powered by Explainable AI
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {stats.map((stat) => {
                    const Icon = stat.icon;
                    const colorClasses = {
                        danger: 'bg-danger-500/10 text-danger-500',
                        warning: 'bg-warning-500/10 text-warning-500',
                        success: 'bg-success-500/10 text-success-500',
                        primary: 'bg-primary-500/10 text-primary-500',
                    };

                    return (
                        <div
                            key={stat.name}
                            className="bg-gray-900 border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors"
                        >
                            <div className="flex items-center justify-between">
                                <div className={cn('p-3 rounded-lg', colorClasses[stat.color as keyof typeof colorClasses])}>
                                    <Icon className="h-6 w-6" />
                                </div>
                                <div className="flex items-center space-x-1 text-sm">
                                    {stat.changeType === 'increase' ? (
                                        <TrendingUp className="h-4 w-4 text-danger-500" />
                                    ) : stat.changeType === 'decrease' ? (
                                        <TrendingDown className="h-4 w-4 text-success-500" />
                                    ) : null}
                                    <span className={cn(
                                        stat.changeType === 'increase' ? 'text-danger-500' :
                                            stat.changeType === 'decrease' ? 'text-success-500' :
                                                'text-gray-500'
                                    )}>
                                        {stat.change}
                                    </span>
                                </div>
                            </div>
                            <div className="mt-4">
                                <div className="text-2xl font-bold text-white">{stat.value}</div>
                                <div className="text-sm text-gray-400 mt-1">{stat.name}</div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* CPU & Memory */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">System Resources</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={metricsHistory}>
                            <defs>
                                <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="time" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                                labelStyle={{ color: '#fff' }}
                            />
                            <Area type="monotone" dataKey="cpu" stroke="#0ea5e9" fillOpacity={1} fill="url(#colorCpu)" />
                            <Area type="monotone" dataKey="memory" stroke="#22c55e" fillOpacity={1} fill="url(#colorMemory)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Request Rate */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Request Rate</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={metricsHistory}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="time" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                                labelStyle={{ color: '#fff' }}
                            />
                            <Line type="monotone" dataKey="requests" stroke="#f59e0b" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Recent Alerts */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Recent Alerts</h3>
                <div className="space-y-3">
                    {alerts?.slice(0, 5).map((alert) => (
                        <div
                            key={alert.id}
                            className="flex items-start space-x-4 p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors"
                        >
                            <div className={cn(
                                'p-2 rounded-lg',
                                alert.severity === 'critical' ? 'bg-danger-500/10 text-danger-500' :
                                    alert.severity === 'high' ? 'bg-warning-500/10 text-warning-500' :
                                        'bg-primary-500/10 text-primary-500'
                            )}>
                                <AlertTriangle className="h-5 w-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between">
                                    <p className="text-sm font-medium text-white truncate">{alert.title}</p>
                                    <span className="text-xs text-gray-500">
                                        {new Date(alert.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-400 mt-1">{alert.message}</p>
                                <div className="flex items-center space-x-4 mt-2">
                                    <span className="text-xs text-gray-500">{alert.source}</span>
                                    {alert.resolved && (
                                        <span className="text-xs text-success-500">Resolved</span>
                                    )}
                                    {alert.acknowledged && !alert.resolved && (
                                        <span className="text-xs text-warning-500">Acknowledged</span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
