import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen">
      <h1 className="text-4xl font-bold mb-8">Sistema de Punto de Venta</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link href="/ventas" 
          className="bg-blue-500 hover:bg-blue-600 text-white rounded-lg p-6 text-center">
          <h2 className="text-2xl font-semibold mb-2">Ventas</h2>
          <p>Registrar nuevas ventas y ver historial</p>
        </Link>
        
        <Link href="/cortes" 
          className="bg-green-500 hover:bg-green-600 text-white rounded-lg p-6 text-center">
          <h2 className="text-2xl font-semibold mb-2">Cortes de Caja</h2>
          <p>Realizar cortes y ver registros anteriores</p>
        </Link>
        
        <Link href="/reportes" 
          className="bg-purple-500 hover:bg-purple-600 text-white rounded-lg p-6 text-center">
          <h2 className="text-2xl font-semibold mb-2">Reportes</h2>
          <p>Ver reportes y estadísticas</p>
        </Link>
      </div>
    </div>
  )
}
