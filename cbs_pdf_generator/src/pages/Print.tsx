import Quotation from '../components/Quotation'
import type { QuotationData } from '../data/quotationData'

function getParam(name: string) {
  const url = new URL(window.location.href)
  return url.searchParams.get(name)
}

function fromBase64Url(b64url: string) {
  let b64 = b64url.replace(/-/g, '+').replace(/_/g, '/')
  while (b64.length % 4) b64 += '='
  const bin = atob(b64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return new TextDecoder().decode(bytes)
}

export default function PrintPage() {
  const encoded = getParam('data') || ''
  let data: QuotationData
  try {
    const json = fromBase64Url(encoded)
    data = JSON.parse(json)
  } catch {
    return <div className="p-6">Invalid or missing data. Provide base64url JSON in ?data=</div>
  }
  return (
    <div className="bg-white print:bg-white">
      <Quotation data={data} />
    </div>
  )
}
