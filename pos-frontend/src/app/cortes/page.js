'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

export default function Cortes() {
  const [cortes, setCortes] = useState([])
  const [nuevoCorte, setNuevoCorte] = useState({
    monto_inicial: '',
    monto_final: '',
    ventas_efectivo: '',
    ventas_tarjeta: '',
    ventas_transferencia: '',
    retiros: '',
    notas: ''
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCortes()
  }, [])

  const fetchCortes = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/cortes')
      const data = await response.json()
      setCortes(data)
      setLoading(false)
    } catch (error) {
      console.error('Error al cargar cortes:', error)
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const corte = {
        ...nuevoCorte,
        monto_inicial: parseFloat(nuevoCorte.monto_inicial),
        monto_final: parseFloat(nuevoCorte.monto_final),
        ventas_efectivo: parseFloat(nuevoCorte.ventas_efectivo || 0),
        ventas_tarjeta: parseFloat(nuevoCorte.ventas_tarjeta || 0),
        ventas_transferencia: parseFloat(nuevoCorte.ventas_transferencia || 0),
        retiros: parseFloat(nuevoCorte.retiros || 0)
      }

      const response = await fetch('http://localhost:5000/api/cortes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(corte)
      })

      if (response.ok) {
        setNuevoCorte({
          monto_inicial: '',
          monto_final: '',
          ventas_efectivo: '',
          ventas_tarjeta: '',
          ventas_transferencia: '',
          retiros: '',
          notas: ''
        })
        fetchCortes()
      }
    } catch (error) {
      console.error('Error al crear corte:', error)
    }
  }

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount)
  }

  if (loading) {
    return <div>Cargando...</div>
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Cortes de Caja</h1>

      {/* Formulario de nuevo corte */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Nuevo Corte</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Monto Inicial
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevoCorte.monto_inicial}
              onChange={(e) => setNuevoCorte({...nuevoCorte, monto_inicial: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Monto Final
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevoCorte.monto_final}
              onChange={(e) => setNuevoCorte({...nuevoCorte, monto_final: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Ventas en Efectivo
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevoCorte.ventas_efectivo}
              onChange={(e) => setNuevoCorte({...nuevoCorte, ventas_efectivo: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Ventas con Tarjeta
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevoCorte.ventas_tarjeta}
              onChange={(e) => setNuevoCorte({...nuevoCorte, ventas_tarjeta: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Ventas por Transferencia
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevoCorte.ventas_transferencia}
              onChange={(e) => setNuevoCorte({...nuevoCorte, ventas_transferencia: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Retiros
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevoCorte.retiros}
              onChange={(e) => setNuevoCorte({...nuevoCorte, retiros: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">
              Notas
            </label>
            <textarea
              value={nuevoCorte.notas}
              onChange={(e) => setNuevoCorte({...nuevoCorte, notas: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              rows="3"
            />
          </div>

          <div className="md:col-span-2">
            <button
              type="submit"
              className="w-full bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
            >
              Registrar Corte
            </button>
          </div>
        </form>
      </div>

      {/* Lista de cortes */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monto Inicial
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monto Final
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ventas Efectivo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ventas Tarjeta
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ventas Transferencia
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Retiros
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {cortes.map((corte) => (
              <tr key={corte._id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  {format(new Date(corte.fecha_hora), 'PPpp', { locale: es })}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(corte.monto_inicial)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(corte.monto_final)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(corte.ventas_efectivo)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(corte.ventas_tarjeta)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(corte.ventas_transferencia)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(corte.retiros)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
