/**
 * Format a number as Indian Rupees.
 * abbreviated=true → ₹84.6M / ₹1.2B / ₹450K
 */
export function formatINR(value: number | null | undefined, abbreviated = false): string {
  if (value === null || value === undefined || isNaN(value)) return '₹0'
  if (abbreviated) {
    const abs = Math.abs(value)
    const sign = value < 0 ? '-' : ''
    if (abs >= 1_000_000_000) return `${sign}₹${(abs / 1_000_000_000).toFixed(1)}B`
    if (abs >= 1_000_000) return `${sign}₹${(abs / 1_000_000).toFixed(1)}M`
    if (abs >= 1_000) return `${sign}₹${(abs / 1_000).toFixed(0)}K`
    return `${sign}₹${abs.toFixed(0)}`
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatUSD(value: number | null | undefined, abbreviated = false): string {
  if (value === null || value === undefined || isNaN(value)) return '$0'
  if (abbreviated) {
    const abs = Math.abs(value)
    const sign = value < 0 ? '-' : ''
    if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(1)}B`
    if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`
    if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`
    return `${sign}$${abs.toFixed(0)}`
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPct(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || isNaN(value)) return '0.0%'
  return `${value.toFixed(decimals)}%`
}


