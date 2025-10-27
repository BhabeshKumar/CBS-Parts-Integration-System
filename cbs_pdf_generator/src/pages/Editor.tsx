import { useMemo, useState, useEffect } from 'react'
import Quotation from '../components/Quotation'
import type { QuotationData, QuotationItem } from '../data/quotationData'
import { quotationData as seed } from '../data/quotationData'
import { isTaxed } from '../utils/money'

// Function to get URL parameters and decode data
function getInitialData(): QuotationData {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const encodedData = urlParams.get('data')
    
    if (encodedData) {
      // Decode base64 data
      const decodedData = atob(encodedData)
      const parsedData = JSON.parse(decodedData)
      
      console.log('Raw parsed data from URL:', parsedData)
      console.log('Carriage in parsed data:', parsedData.carriage)
      
      // Convert abbreviated format to full QuotationData format
      const quotationData: QuotationData = {
        company: {
          name: parsedData.c || parsedData.company || seed.company.name,
          addressLines: seed.company.addressLines,
          email: seed.company.email,
          phone: seed.company.phone,
          vatReg: seed.company.vatReg
        },
        meta: {
          quotationNo: parsedData.quotationNo || parsedData.qn || seed.meta.quotationNo,
          quotationDate: seed.meta.quotationDate,
          validUntil: seed.meta.validUntil,
          customerOrderNo: parsedData.customerOrderNo || seed.meta.customerOrderNo,
          accountRefNo: seed.meta.accountRefNo
        },
        customer: {
          name: parsedData.cu || parsedData.customer || '',
          company: parsedData.ca || parsedData.customer_company || '',
          addressLines: parsedData.caa || parsedData.customer_address || [''],
          email: parsedData.ce || parsedData.customer_email || '',
          phone: parsedData.cp || parsedData.customer_phone || ''
        },
        items: (parsedData.i || parsedData.items || []).map((item: any) => ({
          item: item.item || '',
          code: item.code || '',
          description: item.d || item.description || '',
          quantity: item.q || item.quantity || 1,
          unitPrice: item.p || item.unitPrice || 0,
          taxed: true
        })),
        taxRatePercent: parsedData.t || parsedData.taxRate || seed.taxRatePercent,
        carriage: parsedData.carriage !== undefined ? parsedData.carriage : seed.carriage,
        currency: seed.currency,
        terms: seed.terms,
        acceptanceNote: seed.acceptanceNote,
        footerNote: seed.footerNote
      }
      
      console.log('Loaded data from URL:', quotationData)
      console.log('Carriage/Discount value:', quotationData.carriage)
      return quotationData
    }
  } catch (error) {
    console.error('Error parsing URL data:', error)
  }
  
  return seed
}

function useQuotationState(initial: QuotationData) {
  const [form, setForm] = useState<QuotationData>(initial)

  const subtotal = useMemo(() => form.items.reduce((a, it) => a + it.quantity * it.unitPrice, 0), [form.items])
  const taxable = useMemo(() => form.items.reduce((a, it) => a + (isTaxed(it) ? it.quantity * it.unitPrice : 0), 0), [form.items])
  const tax = useMemo(() => taxable * (form.taxRatePercent / 100), [taxable, form.taxRatePercent])
  const grand = useMemo(() => subtotal + tax + (form.carriage ?? 0), [subtotal, tax, form.carriage])

  function update<K extends keyof QuotationData>(key: K, val: QuotationData[K]) {
    setForm((f) => ({ ...f, [key]: val }))
  }

  function updateItem(index: number, updater: (it: QuotationItem) => QuotationItem) {
    setForm((f) => ({ ...f, items: f.items.map((it, i) => (i === index ? updater(it) : it)) }))
  }

  function addItem() {
    setForm((f) => ({ ...f, items: [...f.items, { item: '', description: '', quantity: 1, unitPrice: 0 }] }))
  }

  function removeItem(index: number) {
    setForm((f) => ({ ...f, items: f.items.filter((_, i) => i !== index) }))
  }

  return { form, setForm, subtotal, tax, grand, update, updateItem, addItem, removeItem }
}

export default function Editor() {
  const initialData = getInitialData()
  const { form, update, updateItem, addItem, removeItem, subtotal, tax, grand } = useQuotationState(initialData)
  const [view, setView] = useState<'edit' | 'preview'>('edit')
  
  // Email functionality state
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false)
  const [emailAddress, setEmailAddress] = useState(form.customer.email || '')
  const [isSendingEmail, setIsSendingEmail] = useState(false)
  const [emailStatus, setEmailStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [emailMessage, setEmailMessage] = useState('')
  
  // Account Ref No visibility toggle
  const [showAccountRef, setShowAccountRef] = useState(!!form.meta.accountRefNo)

  // Email functionality
  const handleSendEmail = async () => {
    if (!emailAddress) {
      setEmailStatus('error')
      setEmailMessage('Please enter a valid email address')
      return
    }

    setIsSendingEmail(true)
    setEmailStatus('idle')
    setEmailMessage('')

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003';
      const response = await fetch(`${API_BASE_URL}/api/email/send-quotation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quotation_data: form,
          customer_email: emailAddress
        })
      })

      const result = await response.json()

      if (result.success) {
        setEmailStatus('success')
        setEmailMessage(`Email sent successfully to ${emailAddress}`)
        setIsEmailModalOpen(false)
      } else {
        setEmailStatus('error')
        setEmailMessage(result.detail || 'Failed to send email')
      }
    } catch (error) {
      setEmailStatus('error')
      setEmailMessage('Failed to connect to email service')
    } finally {
      setIsSendingEmail(false)
    }
  }

  const openEmailModal = () => {
    setEmailAddress(form.customer.email || '')
    setEmailStatus('idle')
    setEmailMessage('')
    setIsEmailModalOpen(true)
  }

  return (
    <div className="min-h-screen bg-neutral-100">
      <div className="max-w-[1400px] mx-auto grid grid-cols-1 xl:grid-cols-2 gap-6 p-6 editor-container">
        {/* Left: form */}
        <div className="bg-white rounded-lg shadow p-6 print:hidden">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-semibold">Quotation Editor</h2>
            <div className="ml-auto flex gap-2">
              <button className="px-3 py-2 rounded bg-neutral-200 hover:bg-neutral-300" onClick={() => setView('edit')}>Edit</button>
              <button className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700" onClick={() => setView('preview')}>Preview</button>
              <button className="px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700" onClick={() => window.print()}>Print</button>
              <button className="px-3 py-2 rounded bg-purple-600 text-white hover:bg-purple-700" onClick={openEmailModal}>📧 Email</button>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basics */}
            <div className="space-y-3">
              <label className="block">
                <span className="text-sm font-medium">Company Name</span>
                <input className="mt-1 input" value={form.company.name} onChange={(e) => update('company', { ...form.company, name: e.target.value })} />
              </label>
              <label className="block">
                <span className="text-sm font-medium">Company Email</span>
                <input className="mt-1 input" value={form.company.email ?? ''} onChange={(e) => update('company', { ...form.company, email: e.target.value })} />
              </label>
              <label className="block">
                <span className="text-sm font-medium">Company Phone</span>
                <input className="mt-1 input" value={form.company.phone ?? ''} onChange={(e) => update('company', { ...form.company, phone: e.target.value })} />
              </label>
              <label className="block">
                <span className="text-sm font-medium">VAT Reg</span>
                <input className="mt-1 input" value={form.company.vatReg ?? ''} onChange={(e) => update('company', { ...form.company, vatReg: e.target.value })} />
              </label>
              <label className="block">
                <span className="text-sm font-medium">Tax Rate (%)</span>
                <input type="number" className="mt-1 input" value={form.taxRatePercent}
                  onChange={(e) => update('taxRatePercent', Number(e.target.value))} />
              </label>
              <label className="block">
                <span className="text-sm font-medium">Carriage</span>
                <input type="number" className="mt-1 input" value={form.carriage ?? 0}
                  onChange={(e) => update('carriage', Number(e.target.value))} />
              </label>
              <label className="block">
                <div className="flex items-center gap-2">
                  <input type="checkbox" checked={showAccountRef} 
                    onChange={(e) => {
                      setShowAccountRef(e.target.checked)
                      if (!e.target.checked) {
                        update('meta', { ...form.meta, accountRefNo: '' })
                      }
                    }} />
                  <span className="text-sm font-medium">Show Account Ref. No.</span>
                </div>
                {showAccountRef && (
                  <input className="mt-1 input" placeholder="Account Reference Number" 
                    value={form.meta.accountRefNo ?? ''} 
                    onChange={(e) => update('meta', { ...form.meta, accountRefNo: e.target.value })} />
                )}
              </label>
            </div>

            {/* Parties */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="font-semibold text-sm">Company Address</div>
                {form.company.addressLines.map((l, i) => (
                  <input key={i} className="input" placeholder={`Address line ${i + 1}`} value={l}
                    onChange={(e) => update('company', { ...form.company, addressLines: form.company.addressLines.map((al, ai) => ai === i ? e.target.value : al) })} />
                ))}
              </div>
              <div className="space-y-3">
                <div className="font-semibold text-sm">Customer</div>
                <input className="input" placeholder="Name" value={form.customer.name}
                  onChange={(e) => update('customer', { ...form.customer, name: e.target.value })} />
                <input className="input" placeholder="Email" value={form.customer.email ?? ''}
                  onChange={(e) => update('customer', { ...form.customer, email: e.target.value })} />
                <input className="input" placeholder="Phone" value={form.customer.phone ?? ''}
                  onChange={(e) => update('customer', { ...form.customer, phone: e.target.value })} />
                {form.customer.addressLines.map((l, i) => (
                  <input key={i} className="input" placeholder={`Address line ${i + 1}`} value={l}
                    onChange={(e) => update('customer', { ...form.customer, addressLines: form.customer.addressLines.map((al, ai) => ai === i ? e.target.value : al) })} />
                ))}
              </div>
            </div>
          </div>

          {/* Items */}
          <div className="mt-8">
            <div className="flex items-center">
              <div className="font-semibold">Items</div>
              <button className="ml-auto px-3 py-2 rounded bg-neutral-200 hover:bg-neutral-300" onClick={addItem}>Add Item</button>
            </div>
            <div className="mt-3 space-y-3">
              {form.items.map((it, i) => (
                <div key={i} className="grid grid-cols-[120px_120px_1fr_90px_120px_80px_40px] gap-2 items-center">
                  <input className="input" placeholder="Item" value={it.item} onChange={(e) => updateItem(i, (o) => ({ ...o, item: e.target.value }))} />
                  <input className="input" placeholder="Code" value={it.code ?? ''} onChange={(e) => updateItem(i, (o) => ({ ...o, code: e.target.value }))} />
                  <input className="input" placeholder="Description" value={it.description} onChange={(e) => updateItem(i, (o) => ({ ...o, description: e.target.value }))} />
                  <input type="number" className="input text-right" placeholder="Qty" value={it.quantity} onChange={(e) => updateItem(i, (o) => ({ ...o, quantity: Number(e.target.value) }))} />
                  <input type="number" className="input text-right" placeholder="Unit Price" value={it.unitPrice} onChange={(e) => updateItem(i, (o) => ({ ...o, unitPrice: Number(e.target.value) }))} />
                  <input className="input text-center" placeholder="Taxable (X or blank)" value={it.taxable ?? (it.taxed ? 'X' : '')}
                    onChange={(e) => updateItem(i, (o) => ({ ...o, taxable: e.target.value }))} />
                  <button className="h-10 rounded bg-red-50 hover:bg-red-100 text-red-700" onClick={() => removeItem(i)}>✕</button>
                </div>
              ))}
            </div>
          </div>

          {/* Terms */}
          <div className="mt-8">
            <div className="font-semibold">Terms and Conditions</div>
            <div className="mt-2 space-y-2">
              {form.terms.map((t, i) => (
                <input key={i} className="input" value={t}
                  onChange={(e) => update('terms', form.terms.map((tt, ii) => (ii === i ? e.target.value : tt)))} />
              ))}
            </div>
          </div>

          {/* Footer lines */}
          <div className="mt-8 grid gap-3">
            <input className="input" value={form.acceptanceNote ?? ''} onChange={(e) => update('acceptanceNote', e.target.value)} />
            <input className="input" value={form.footerNote ?? ''} onChange={(e) => update('footerNote', e.target.value)} />
          </div>

          {/* Auto totals */}
          <div className="mt-8 grid grid-cols-3 gap-4 text-sm">
            <div className="rounded bg-neutral-50 p-3">Subtotal: <strong>{subtotal.toLocaleString(undefined, { style: 'currency', currency: 'USD' })}</strong></div>
            <div className="rounded bg-neutral-50 p-3">Tax: <strong>{tax.toLocaleString(undefined, { style: 'currency', currency: form.currency || 'GBP' })}</strong></div>
            <div className="rounded bg-neutral-50 p-3">Grand Total: <strong>{grand.toLocaleString(undefined, { style: 'currency', currency: form.currency || 'GBP' })}</strong></div>
          </div>
        </div>

        {/* Right: live preview */}
        <div className={view === 'preview' ? '' : 'opacity-100'}>
          <Quotation data={form} />
        </div>
      </div>

      {/* Email Modal */}
      {isEmailModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Send Quotation Email</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Customer Email Address</label>
              <input
                type="email"
                value={emailAddress}
                onChange={(e) => setEmailAddress(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="sales@concretebatchingsystems.com"
              />
            </div>

            {emailMessage && (
              <div className={`mb-4 p-3 rounded-md ${
                emailStatus === 'success' ? 'bg-green-100 text-green-700' : 
                emailStatus === 'error' ? 'bg-red-100 text-red-700' : 
                'bg-blue-100 text-blue-700'
              }`}>
                {emailMessage}
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setIsEmailModalOpen(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={isSendingEmail}
              >
                Cancel
              </button>
              <button
                onClick={handleSendEmail}
                disabled={isSendingEmail || !emailAddress}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSendingEmail ? 'Sending...' : 'Send Email'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// handy utility classes
// Using Tailwind v4 via @import, but we add a few small utilities
// here with global CSS from index.css.
