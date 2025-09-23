import QuotationCBS from "./quotation/QuotationCBS";
import type { QuotationData } from "../data/quotationData";

export default function Quotation({ data }: { data: QuotationData }) {
  return <QuotationCBS data={data} />
}
