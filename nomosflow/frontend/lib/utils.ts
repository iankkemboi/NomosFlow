import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

export function formatDate(dateStr: string): string {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(dateStr));
}

export function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 30) return `${diffDays}d ago`;
  return formatDate(dateStr);
}

export function riskLevelColor(risk: string): string {
  switch (risk) {
    case "critical": return "text-red-600 bg-red-50 border-red-200";
    case "high":     return "text-orange-600 bg-orange-50 border-orange-200";
    case "medium":   return "text-amber-600 bg-amber-50 border-amber-200";
    case "low":      return "text-green-600 bg-green-50 border-green-200";
    default:         return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "paid":        return "text-green-700 bg-green-50 border-green-200";
    case "failed":      return "text-red-700 bg-red-50 border-red-200";
    case "retrying":    return "text-blue-700 bg-blue-50 border-blue-200";
    case "pending":     return "text-amber-700 bg-amber-50 border-amber-200";
    case "written_off": return "text-gray-700 bg-gray-100 border-gray-200";
    case "active":      return "text-green-700 bg-green-50 border-green-200";
    case "suspended":   return "text-orange-700 bg-orange-50 border-orange-200";
    case "cancelled":   return "text-red-700 bg-red-50 border-red-200";
    default:            return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

export function deviceLabel(deviceType: string): string {
  switch (deviceType) {
    case "ev":         return "EV";
    case "heat_pump":  return "Heat Pump";
    case "battery":    return "Battery";
    default:           return deviceType;
  }
}
