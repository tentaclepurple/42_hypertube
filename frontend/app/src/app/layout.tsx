import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "./ui/components/navbar";
import Footer from "./ui/components/footer";
import { AuthProvider } from "./context/authcontext";
import { I18nProvider } from "./ui/components/i18nProvider";
import Script from "next/script";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HYPERTUBE",
  description: "Your movie application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="color-scheme" content="dark" />
        <Script id="hide-nextjs-badge" strategy="beforeInteractive">
          {`
            (function() {
              const style = document.createElement('style');
              style.innerHTML = '[data-nextjs-toast], [data-next-badge-root], .nextjs-toast { display: none !important; }';
              document.head.appendChild(style);
              
              if (typeof window !== 'undefined') {
                const observer = new MutationObserver(() => {
                  document.querySelectorAll('[data-nextjs-toast], [data-next-badge-root], .nextjs-toast').forEach(el => {
                    el.style.display = 'none';
                    el.remove();
                  });
                });
                observer.observe(document.body, { childList: true, subtree: true });
              }
            })();
          `}
        </Script>
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex flex-col min-h-screen bg-[#0a0a0a] text-[#ededed]`}
      >
        <I18nProvider>
          <AuthProvider>
            <Navbar />
            <main className="flex-grow">{children}</main>
            <Footer />
          </AuthProvider>
        </I18nProvider>
      </body>
    </html>
  );
}