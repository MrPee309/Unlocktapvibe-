import './globals.css'
import { Providers } from './providers'

export const metadata = {
  title: 'UnlockTap — Apple IMEI & Serial Number Checker',
  description: 'Instant Apple device verification. Check IMEI and serial numbers for iCloud lock, blacklist, warranty, carrier and more.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{__html:'window.addEventListener("error",function(e){if(e.error instanceof DOMException&&e.error.name==="DataCloneError"&&e.message&&e.message.includes("PerformanceServerTiming")){e.stopImmediatePropagation();e.preventDefault()}},true);'}} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}