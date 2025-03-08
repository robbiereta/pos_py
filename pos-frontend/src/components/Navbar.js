import Link from 'next/link'

export default function Navbar() {
  return (
    <nav className="bg-gray-800 text-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold">
              POS System
            </Link>
          </div>
          <div className="flex space-x-4">
            <Link href="/ventas" className="hover:text-gray-300">
              Ventas
            </Link>
            <Link href="/cortes" className="hover:text-gray-300">
              Cortes
            </Link>
            <Link href="/reportes" className="hover:text-gray-300">
              Reportes
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
