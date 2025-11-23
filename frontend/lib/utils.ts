import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get the API base URL based on the environment
 * In production (Vercel), use relative URLs (empty string)
 * In development, use localhost:8000
 */
export function getApiBaseUrl(): string {
  // If explicitly set via environment variable, use that
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  
  // Check if we're in the browser
  if (typeof window !== 'undefined') {
    // Client-side: check if we're on localhost (development)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000'
    }
    // Production: use relative URLs (Vercel will route /api/* to the API handler)
    return ''
  }
  
  // Server-side: use relative URL for production, localhost for dev
  return process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000'
}

