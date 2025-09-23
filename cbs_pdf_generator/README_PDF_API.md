# PDF API (Dev)

Start both the Vite app and the PDF server:

```
npm run pdf:dev
```

POST your quotation JSON to generate a PDF:

```
POST http://localhost:5173/api/quote/pdf
Content-Type: application/json

{ ...QuotationData }
```

Response is `application/pdf` rendered via the `/print` route.
