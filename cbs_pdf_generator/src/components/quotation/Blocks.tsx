import type { PropsWithChildren, ReactNode } from 'react'

export function Page({ children }: PropsWithChildren) {
  return <div className="print-a4 bg-white text-gray-900 relative mx-auto">{children}</div>
}

export function Container({ children }: PropsWithChildren) {
  return <div className="px-[16px] pt-[16px] print:px-[4mm] print:pt-[2mm]">{children}</div>
}

export function Header({ title, right }: { title: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-start">
      <h1 className="text-[48px] font-semibold tracking-wide text-gray-600">{title}</h1>
      <div className="ml-auto text-right">{right}</div>
    </div>
  )
}

export function KeyValue({ label, value }: { label: ReactNode; value: ReactNode }) {
  return (
    <div>
      <span className="font-semibold">{label}</span> {value}
    </div>
  )
}

export function Party({ heading, name, company, addressLines, align = 'left' as 'left' | 'right' }:
  { heading: ReactNode; name: string; company?: string; addressLines?: string[]; align?: 'left' | 'right' }) {
  return (
    <div className={align === 'right' ? 'text-right' : ''}>
      <div className="font-bold">{heading}</div>
      <div className="mt-1">
        <div className="font-semibold">{name}</div>
        {company && <div>{company}</div>}
        {addressLines?.map((l: string, i: number) => (
          <div key={i}>{l}</div>
        ))}
      </div>
    </div>
  )
}

export function GridTable({ columns, children }: { columns: string; children: ReactNode }) {
  return <div className={`grid border border-gray-300 ${columns}`}>{children}</div>
}

export function Th({ children, dense }: PropsWithChildren & { dense?: boolean }) {
  return (
    <div className={`px-2 ${dense ? 'py-1 text-[11px]' : 'py-2 text-[12px]'} font-semibold border-b border-gray-300 text-white`} style={{backgroundColor: '#1177C1'}}>
      {children}
    </div>
  )
}

export function Td({ children, right, border = true, dense, alt }: { children: ReactNode; right?: boolean; border?: boolean; dense?: boolean; alt?: boolean }) {
  return (
    <div 
      className={`px-2 ${dense ? 'py-2 min-h-[40px]' : 'py-4 min-h-[56px]'} ${border ? 'border-r border-gray-200' : ''} ${right ? 'text-right' : ''}`}
      style={{backgroundColor: alt ? '#E8F2FF' : '#FFFFFF'}}
    >
      {children}
    </div>
  )
}

export function TotalsRow({ label, value, bold, shaded }: { label: ReactNode; value: ReactNode; bold?: boolean; shaded?: boolean }) {
  return (
    <>
      <div></div>
      <div className={`border-l border-t border-gray-300 px-3 py-2 text-right ${shaded ? 'bg-gray-100' : 'bg-gray-50'} ${bold ? 'font-bold text-blue-700' : 'font-semibold'}`}>{label}</div>
      <div className={`border-t border-gray-300 px-3 py-2 text-right ${shaded ? 'bg-gray-100' : 'bg-gray-50'} ${bold ? 'font-bold text-blue-700' : ''}`}>{value}</div>
    </>
  )
}
