import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "ScholarAgent - AI-Powered Research Assistant",
  description:
    "Search academic papers across arXiv and PubMed with an AI agent that retrieves, grades, and synthesizes research findings.",
  keywords: ["research", "AI", "arxiv", "pubmed", "academic", "papers"],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
