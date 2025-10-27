// All changeable details for the Sales Quotation live here
export type QuotationParty = {
  name: string;
  company?: string;
  addressLines: string[];
  email?: string;
  phone?: string;
};

export type QuotationItem = {
  item: string;
  code?: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxed?: boolean;
  // Alternate input: if provided as 'X' (case-insensitive), item is taxable
  taxable?: string;
};

export type CompanyInfo = {
  name: string;
  addressLines: string[];
  email?: string;
  phone?: string;
  vatReg?: string;
};

export type QuotationMeta = {
  accountRefNo?: string;
  customerOrderNo?: string;
  quotationNo: string;
  quotationDate: string;
  validUntil?: string;
};

export type QuotationData = {
  company: CompanyInfo;
  meta: QuotationMeta;
  customer: QuotationParty;
  items: QuotationItem[];
  taxRatePercent: number;
  carriage?: number;
  currency?: string;
  terms: string[];
  acceptanceNote?: string;
  footerNote?: string;
  email?: string;
};

export const quotationData: QuotationData = {
  company: {
    name: "CONCRETE Batching Systems Ltd.",
    addressLines: ["140 Markethill Road", "Armagh, Co. Armagh", "BT60 1LF"],
    email: "purchasing@concretebatchingsystems.com",
    phone: "+44 (0)28 3082 1172",
    vatReg: "978324675",
  },
  meta: {
    accountRefNo: "",
    customerOrderNo: "",
    quotationNo: "QB-00123",
    quotationDate: "2025-08-19",
    validUntil: "2025-09-19",
  },
  customer: {
    name: "Customer's Name",
    addressLines: ["Delivery Address Line 1", "Line 2", "Line 3"],
    email: "customer@email.com",
    phone: "+44 0000 000000",
  },
  items: [
    {
      item: "Material 1",
      code: "M1",
      description: "Material 1",
      quantity: 2,
      unitPrice: 120,
      taxed: true,
    },
    {
      item: "Material 2",
      code: "M2",
      description: "Material 2",
      quantity: 3,
      unitPrice: 35,
      taxed: false,
    },
    {
      item: "Labour 1",
      code: "L1",
      description: "Labour 1",
      quantity: 1,
      unitPrice: 1000,
      taxed: true,
    },
    {
      item: "Plant 1",
      code: "P1",
      description: "Plant 1",
      quantity: 6,
      unitPrice: 80,
      taxed: false,
    },
  ],
  taxRatePercent: 20,
  carriage: 0,
  currency: "GBP",
  terms: [
    "Customer will be billed after indicating acceptance of this Sales Quotation.",
    "Payment will be due prior to delivery of the service/goods.",
    "Please return the signed Sales Quotation to the address above.",
  ],
  acceptanceNote: "Customer Acceptance (sign below)",
  footerNote:
    "If you have any question about this Sales Quotation, please contact:",
  email: "sales@concretebatchingsystems.com"
};
