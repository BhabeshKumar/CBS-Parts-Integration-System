import express, { type Request, type Response } from 'express'
import cors from 'cors'
import { createServer as createViteServer } from 'vite'

async function createServer() {
  const app = express()
  app.use(cors())
  app.use(express.json({ limit: '2mb' }))

  // Health
  app.get('/health', (_req: Request, res: Response) => res.send('ok'))

  // REST endpoint to render PDF
  app.post('/api/quote/pdf', async (req: Request, res: Response) => {
    try {
  console.log('POST /api/quote/pdf')
      const body = req.body as any // JSON submitted by client

      // Generate an Account Ref No if not provided in body.meta.accountRefNo
      const generateAccountRefNo = () => {
        const now = new Date()
        const yyyy = now.getFullYear()
        const mm = String(now.getMonth() + 1).padStart(2, '0')
        const dd = String(now.getDate()).padStart(2, '0')
        const hh = String(now.getHours()).padStart(2, '0')
        const mi = String(now.getMinutes()).padStart(2, '0')
        const ss = String(now.getSeconds()).padStart(2, '0')
        const rand = Math.random().toString(36).slice(2, 6).toUpperCase()
        return `AR-${yyyy}${mm}${dd}-${hh}${mi}${ss}-${rand}`
      }

      const providedRef = body?.meta?.accountRefNo
      const accountRefNo: string = (typeof providedRef === 'string' && providedRef.trim()) ? providedRef.trim() : generateAccountRefNo()

      // Inject the accountRefNo into data used for printing
      const data = { ...body, meta: { ...(body?.meta || {}), accountRefNo } }
      // Encode data into base64url and open the /print page in a headless browser to render to PDF
      const { toBase64Url } = await import('../src/utils/base64url.ts')
      const encoded = toBase64Url(JSON.stringify(data))

      // Use Puppeteer to render
      const puppeteer = await import('puppeteer')
      const browser = await puppeteer.launch({ 
        headless: 'new' as any,
        executablePath: '/usr/bin/chromium-browser',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      })
      const page = await browser.newPage()

      // Build local URL; assumes app is served by this same Express + Vite on localhost:5173 equivalently
      const origin = `http://${process.env.CBS_DOMAIN || 'localhost'}:5173` // Dynamic domain for production
      const url = `${origin}/print?data=${encoded}`
      await page.goto(url, { waitUntil: 'networkidle0' })
      const pdf = await page.pdf({ format: 'A4', printBackground: true, margin: { top: '10mm', right: '10mm', bottom: '10mm', left: '10mm' } })

      await browser.close()

  // Build a safe filename using the accountRefNo
  const safeName = String(accountRefNo)
    .replace(/[^a-zA-Z0-9-_.]/g, '-')
    .replace(/-+/g, '-')
  const filename = `${safeName || 'quotation'}.pdf`

  res.setHeader('Content-Type', 'application/pdf')
  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`)
  res.send(Buffer.from(pdf))
    } catch (err: any) {
      console.error(err)
      res.status(500).json({ error: 'Failed to generate PDF', details: String(err?.message || err) })
    }
  })

  // Dev: use Vite middleware to serve the client app and /print route AFTER API routes.
  const vite = await createViteServer({ server: { middlewareMode: true } })
  app.use(vite.middlewares)

  const port = Number(process.env.PORT || 5173)
  app.listen(port, () => console.log(`Server listening on http://localhost:${port}`))
}

createServer()
