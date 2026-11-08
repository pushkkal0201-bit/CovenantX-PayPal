import './globals.css';
import type {Metadata} from 'next';
export const metadata:Metadata={title:'CovenantX · Financial Assurance',description:'Trace contractual evidence to an approved sandbox settlement.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
