'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

export default function Ventas() {
  const [ventas, setVentas] = useState([])
  const [nuevaVenta, setNuevaVenta] = useState({
    amount: '',
    payment_method: 'efectivo',
    notes: ''
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVentas()
  }, [])

  const fetchVentas = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/ventas')
      const data = await response.json()
      setVentas(data)
      setLoading(false)
    } catch (error) {
      console.error('Error al cargar ventas:', error)
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const venta = {
        ...nuevaVenta,
        timestamp: new Date().toISOString(),
        amount: parseFloat(nuevaVenta.amount)
      }

      const response = await fetch('http://localhost:5000/api/ventas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(venta)
      })

      if (response.ok) {
        setNuevaVenta({
          amount: '',
          payment_method: 'efectivo',
          notes: ''
        })
        fetchVentas()
      }
    } catch (error) {
      console.error('Error al crear venta:', error)
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
      <h1 className="text-3xl font-bold mb-8">Ventas</h1>

      {/* Formulario de nueva venta */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Nueva Venta</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Monto
            </label>
            <input
              type="number"
              step="0.01"
              value={nuevaVenta.amount}
              onChange={(e) => setNuevaVenta({...nuevaVenta, amount: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Método de Pago
            </label>
            <select
              value={nuevaVenta.payment_method}
              onChange={(e) => setNuevaVenta({...nuevaVenta, payment_method: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="efectivo">Efectivo</option>
              <option value="tarjeta">Tarjeta</option>
              <option value="transferencia">Transferencia</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Notas
            </label>
            <textarea
              value={nuevaVenta.notes}
              onChange={(e) => setNuevaVenta({...nuevaVenta, notes: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              rows="3"
            />
          </div>

          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
          >
            Registrar Venta
          </button>
        </form>
      </div>

      {/* Lista de ventas */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monto
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Método de Pago
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Notas
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {ventas.map((venta) => (
              <tr key={venta._id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  {format(new Date(venta.timestamp), 'PPpp', { locale: es })}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {formatMoney(venta.amount)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap capitalize">
                  {venta.payment_method}
                </td>
                <td className="px-6 py-4">
                  {venta.notes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
