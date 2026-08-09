import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ORBIT — Autonomous Intelligence Mission Control',
  description: 'High-performance mission control interface for autonomous AI agents.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090a0f] text-zinc-100 antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
