import type { QuotationData } from "../../data/quotationData";
import {
  fmt,
  totals,
  currency as defaultCurrency,
  isTaxed,
} from "../../utils/money";
import { Container, GridTable, Header, KeyValue, Page, Td, Th } from "./Blocks";

export default function QuotationCBS({ data }: { data: QuotationData }) {
  const ccy = data.currency || defaultCurrency;
  const { sub, tax, grand } = totals(
    data.items,
    data.taxRatePercent,
    data.carriage ?? 0
  );

  return (
    <Page>
      <Container>
        <div className="flex items-start gap-6">
          <div className="flex-1">
            {/* Faux logo */}
            <div className="w-[400px] h-[52px] rounded mb-2 drop-shadow-xl">
              <img src="CBS_Logo.png" className="w-full h-full" alt="" />
            </div>
            <Header
              title={
                <span className="text-blue-700 text-[42px]">
                  Sales Quotation
                </span>
              }
              right={
                <div className="text-[13px] space-y-1">
                  <KeyValue
                    label="Account Ref. No.:"
                    value={data.meta.accountRefNo || ""}
                  />
                  <KeyValue
                    label="Quotation No.:"
                    value={data.meta.quotationNo}
                  />
                  <KeyValue
                    label="Quotation Date:"
                    value={data.meta.quotationDate}
                  />
                  <KeyValue
                    label="Valid Until:"
                    value={data.meta.validUntil || ""}
                  />
                </div>
              }
            />

            {/* Company details */}
            <div className="mt-2 text-[13px] text-gray-700">
              {data.company.addressLines.map((l, i) => (
                <div key={i}>{l}</div>
              ))}
              {data.company.email && <div>Email: {data.company.email}</div>}
              {data.company.phone && <div>Phone No.: {data.company.phone}</div>}
              {data.company.vatReg && (
                <div>VAT Reg No: {data.company.vatReg}</div>
              )}
            </div>

            {/* Customer block */}
            <div className="mt-4 border border-gray-300">
              <div
                className="text-white px-3 py-2 font-semibold border-2 border-black"
                style={{ color: "#1177C1" }}
              >
                Customer's Name
              </div>
              <div className="p-3 space-y-2 text-[13px]">
                <div className="font-medium">{data.customer.name}</div>
                <div className="text-gray-700">
                  {data.customer.addressLines.map((l, i) => (
                    <div key={i}>{l}</div>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-gray-700">
                    Customer's Email: {data.customer.email || ""}
                  </div>
                  <div className="text-gray-700">
                    Customer's Phone No.: {data.customer.phone || ""}
                  </div>
                </div>
              </div>
            </div>

            {/* Items Table */}
            <div className="mt-4">
              <GridTable columns="grid-cols-[120px_120px_1fr_100px_150px_150px]">
                {[
                  "Quantity Ordered",
                  "Product Code",
                  "Product Description",
                  "Taxed",
                  "Unit Price",
                  "Total",
                ].map((h) => (
                  <Th key={h} dense>
                    {h}
                  </Th>
                ))}

                {data.items.map((it, idx) => {
                  const isAlt = idx % 2 === 1;
                  return (
                    <>
                      <Td right dense alt={isAlt}>
                        {it.quantity}
                      </Td>
                      <Td dense alt={isAlt}>
                        {it.code || ""}
                      </Td>
                      <Td dense alt={isAlt}>
                        {it.description}
                      </Td>
                      <Td right dense alt={isAlt}>
                        {isTaxed(it) ? "X" : ""}
                      </Td>
                      <Td right dense alt={isAlt}>
                        {fmt(it.unitPrice, ccy)}
                      </Td>
                      <Td right border={false} dense alt={isAlt}>
                        {fmt(it.quantity * it.unitPrice, ccy)}
                      </Td>
                    </>
                  );
                })}

                <div className="col-span-6 grid grid-cols-[1fr_220px_180px]">
                  <div className="border-t border-gray-300">
                    {/* Terms moved below into the acceptance area */}
                    <div className="mt-4"></div>
                  </div>
                  <div className="border-l border-t border-gray-300 px-3 py-2 text-right bg-gray-50 font-semibold">
                    Sub-Total
                  </div>
                  <div className="border-t border-gray-300 px-3 py-2 text-right bg-gray-50">
                    {fmt(sub, ccy)}
                  </div>

                  <div></div>
                  <div className="border-l border-t border-gray-300 px-3 py-2 text-right bg-gray-50 font-semibold">
                    Taxable
                  </div>
                  <div className="border-t border-gray-300 px-3 py-2 text-right bg-gray-50">
                    {fmt(
                      data.items
                        .filter((i) => isTaxed(i))
                        .reduce((a, b) => a + b.quantity * b.unitPrice, 0),
                      ccy
                    )}
                  </div>

                  <div></div>
                  <div className="border-l border-t border-gray-300 px-3 py-2 text-right bg-gray-50 font-semibold">
                    Tax Rate
                  </div>
                  <div className="border-t border-gray-300 px-3 py-2 text-right bg-gray-50">
                    {data.taxRatePercent}%
                  </div>

                  <div></div>
                  <div className="border-l border-t border-gray-300 px-3 py-2 text-right bg-gray-50 font-semibold">
                    Tax Due
                  </div>
                  <div className="border-t border-gray-300 px-3 py-2 text-right bg-gray-50">
                    {fmt(tax, ccy)}
                  </div>

                  <div></div>
                  <div className="border-l border-t border-gray-300 px-3 py-2 text-right bg-gray-50 font-semibold">
                    {(data.carriage ?? 0) < 0 ? "Discount" : "Carriage"}
                  </div>
                  <div className="border-t border-gray-300 px-3 py-2 text-right bg-gray-50">
                    {fmt(data.carriage ?? 0, ccy)}
                  </div>

                  <div></div>
                  <div
                    className="border-l border-t border-gray-300 px-3 py-3 text-right text-white font-bold"
                    style={{ backgroundColor: "#1177C1" }}
                  >
                    GRAND TOTAL
                  </div>
                  <div
                    className="border-t border-gray-300 px-3 py-3 text-right text-white font-bold"
                    style={{ backgroundColor: "#1177C1" }}
                  >
                    {fmt(grand, ccy)}
                  </div>
                </div>
              </GridTable>
            </div>

            {/* Terms and acceptance moved under totals (replacing signature area) */}
            <div className="mt-6 border border-gray-300">
              <div
                className="text-white px-3 py-2 font-semibold text-center"
                style={{ backgroundColor: "#1177C1" }}
              >
                Terms and Conditions
              </div>
              <ol className="p-4 text-[13px] list-decimal pl-8 space-y-2 text-gray-800">
                {data.terms.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ol>
              <div className="px-4 pb-4 text-[13px] text-gray-700 font-bold">
                By accepting this Sales Quotation you confirm your acceptance of
                the terms above and consent to the provision of the
                goods/services described.
              </div>
            </div>

            <div className="mt-4 text-[16px] text-gray-700 text-center">
              {data.footerNote}
            </div>
            <div className="mt-4 py-4 text-[20px] text-gray-700 text-center font-bold bg-blue-200">
              {data.email ?? "sampleemail@gmail.com"}
            </div>
            <div className="mt-4 text-[16px] text-gray-700 text-center">
              Thank you!
            </div>
          </div>
        </div>
      </Container>
    </Page>
  );
}
