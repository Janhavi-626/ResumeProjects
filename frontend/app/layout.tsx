import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Returns Operations | Decision Assistant",
  description: "Evidence-led returns investigation and approval console.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}