import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
}

export function formatNumber(num: number, decimals: number = 2): string {
    return num.toFixed(decimals);
}

export function getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
        critical: 'text-danger-500 bg-danger-500/10',
        high: 'text-warning-500 bg-warning-500/10',
        medium: 'text-primary-500 bg-primary-500/10',
        low: 'text-success-500 bg-success-500/10',
    };
    return colors[severity] || colors.medium;
}
