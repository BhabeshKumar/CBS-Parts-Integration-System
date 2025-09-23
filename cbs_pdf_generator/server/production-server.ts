import express, { type Request, type Response } from 'express'
import cors from 'cors'
import path from 'path'
import fs from 'fs'
import { createServer as createViteServer } from 'vite'

// Production-ready server with error handling and monitoring
async function createProductionServer() {
  const app = express()
  const isProduction = process.env.NODE_ENV === 'production'
  
  // Global error handlers
  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error)
    // Don't exit in production, log and continue
    if (!isProduction) {
      process.exit(1)
    }
  })

  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason)
    // Don't exit in production, log and continue
  })

  // Middleware
  app.use(cors({
    origin: true,
    credentials: true
  }))
  app.use(express.json({ limit: '5mb' }))
  app.use(express.urlencoded({ extended: true }))

  // Request logging
  app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.url}`)
    next()
  })

  // Health check endpoint
  app.get('/health', (_req: Request, res: Response) => {
    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      environment: process.env.NODE_ENV || 'development'
    })
  })

  // Enhanced PDF generation with proper error handling and cleanup
  app.post('/api/quote/pdf', async (req: Request, res: Response) => {
    let browser = null
    try {
      console.log('PDF generation request received')
      const body = req.body as any

      // Validate request body
      if (!body || typeof body !== 'object') {
        return res.status(400).json({ error: 'Invalid request body' })
      }

      // Generate Account Ref No
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
      const accountRefNo: string = (typeof providedRef === 'string' && providedRef.trim()) 
        ? providedRef.trim() 
        : generateAccountRefNo()

      // Prepare data
      const data = { ...body, meta: { ...(body?.meta || {}), accountRefNo } }
      
      // Encode data
      const { toBase64Url } = await import('../src/utils/base64url.ts')
      const encoded = toBase64Url(JSON.stringify(data))

      // Use Puppeteer with production settings
      const puppeteer = await import('puppeteer')
      
      // Production browser launch options
      const browserOptions = {
        headless: 'new' as any,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu',
          '--disable-extensions',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-renderer-backgrounding'
        ],
        timeout: 30000
      }

      browser = await puppeteer.launch(browserOptions)
      const page = await browser.newPage()

      // Set viewport and timeout
      await page.setViewport({ width: 1200, height: 800 })
      page.setDefaultTimeout(20000)

      // Determine the correct base URL
      const host = req.get('host') || 'localhost:5173'
      const protocol = req.secure || req.get('x-forwarded-proto') === 'https' ? 'https' : 'http'
      const baseUrl = process.env.BASE_URL || `${protocol}://${host}`
      
      const url = `${baseUrl}/print?data=${encoded}`
      console.log(`Generating PDF from: ${url}`)

      // Navigate with retry logic
      let retries = 3
      while (retries > 0) {
        try {
          await page.goto(url, { 
            waitUntil: 'networkidle0',
            timeout: 15000
          })
          break
        } catch (error) {
          retries--
          if (retries === 0) throw error
          console.log(`Retrying navigation... (${retries} retries left)`)
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }

      // Wait for content to be ready
      await page.waitForSelector('body', { timeout: 10000 })

      // Generate PDF
      const pdf = await page.pdf({
        format: 'A4',
        printBackground: true,
        margin: { 
          top: '10mm', 
          right: '10mm', 
          bottom: '10mm', 
          left: '10mm' 
        }
      })

      await browser.close()
      browser = null

      // Generate safe filename
      const safeName = String(accountRefNo)
        .replace(/[^a-zA-Z0-9-_.]/g, '-')
        .replace(/-+/g, '-')
      const filename = `${safeName || 'quotation'}.pdf`

      // Send response
      res.setHeader('Content-Type', 'application/pdf')
      res.setHeader('Content-Disposition', `attachment; filename="${filename}"`)
      res.setHeader('Content-Length', pdf.length)
      res.send(Buffer.from(pdf))

      console.log(`PDF generated successfully: ${filename}`)

    } catch (err: any) {
      console.error('PDF generation error:', err)
      
      // Ensure browser is closed
      if (browser) {
        try {
          await browser.close()
        } catch (closeError) {
          console.error('Error closing browser:', closeError)
        }
      }

      // Send error response
      const errorMessage = err?.message || 'Unknown error'
      res.status(500).json({ 
        error: 'Failed to generate PDF', 
        details: errorMessage,
        timestamp: new Date().toISOString()
      })
    }
  })

  if (isProduction) {
    // Production: serve built static files
    const distPath = path.join(__dirname, '../dist')
    if (fs.existsSync(distPath)) {
      app.use(express.static(distPath))
      
      // Serve index.html for all non-API routes
      app.get('*', (req, res) => {
        if (!req.path.startsWith('/api/')) {
          res.sendFile(path.join(distPath, 'index.html'))
        } else {
          res.status(404).json({ error: 'API endpoint not found' })
        }
      })
    } else {
      console.error('Build directory not found:', distPath)
      process.exit(1)
    }
  } else {
    // Development: use Vite middleware
    try {
      const vite = await createViteServer({ 
        server: { middlewareMode: true },
        appType: 'spa'
      })
      app.use(vite.middlewares)
    } catch (error) {
      console.error('Failed to create Vite server:', error)
      process.exit(1)
    }
  }

  // 404 handler
  app.use('*', (req, res) => {
    res.status(404).json({ error: 'Route not found' })
  })

  // Global error handler
  app.use((err: any, req: Request, res: Response, next: any) => {
    console.error('Express error:', err)
    res.status(500).json({ 
      error: 'Internal server error',
      timestamp: new Date().toISOString()
    })
  })

  const port = Number(process.env.PORT || 5173)
  const host = process.env.HOST || '0.0.0.0'

  const server = app.listen(port, host, () => {
    console.log(`🚀 CBS Quotation Generator running on http://${host}:${port}`)
    console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`)
    console.log(`💾 Memory usage: ${JSON.stringify(process.memoryUsage(), null, 2)}`)
  })

  // Graceful shutdown
  const shutdown = (signal: string) => {
    console.log(`\n${signal} received. Shutting down gracefully...`)
    server.close(() => {
      console.log('Server closed.')
      process.exit(0)
    })
  }

  process.on('SIGTERM', () => shutdown('SIGTERM'))
  process.on('SIGINT', () => shutdown('SIGINT'))

  return server
}

// Start server
createProductionServer().catch(error => {
  console.error('Failed to start server:', error)
  process.exit(1)
})
