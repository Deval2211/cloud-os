import type { Metadata } from 'next';
import './layout.css';
import '@/globals.css';

export const metadata: Metadata = {
  title: 'Cloud OS - Browser-based Operating System for AI Development',
  description: 'Universal Cloud OS: GPU orchestration, workflow automation, and AI development in your browser',
  viewport: 'width=device-width, initial-scale=1, maximum-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#0c3d66" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body>
        <div id="root">{children}</div>
      </body>
    </html>
  );
}
