export const currency = 'USD'
export function fmt(n: number, c: string = currency) {
  return n.toLocaleString(undefined, { style: 'currency', currency: c })
}
export function subtotal(items: { quantity: number; unitPrice: number }[]) {
  return items.reduce((a, it) => a + it.quantity * it.unitPrice, 0)
}
export type TaxFlags = { taxed?: boolean; taxable?: string }

export function isTaxed(it: TaxFlags) {
  if (it.taxed) return true
  const mark = (it.taxable || '').trim().toUpperCase()
  return mark === 'X'
}
export function taxableSubtotal(items: { quantity: number; unitPrice: number }[] & TaxFlags[]) {
  return (items as any[]).reduce((a, it: any) => a + (isTaxed(it) ? it.quantity * it.unitPrice : 0), 0)
}
export function totals(items: ({ quantity: number; unitPrice: number } & TaxFlags)[], taxRatePercent: number, carriage = 0) {
  const sub = subtotal(items)
  const taxable = taxableSubtotal(items)
  const tax = taxable * (taxRatePercent / 100)
  const grand = sub + tax + carriage
  return { sub, tax, grand }
}
