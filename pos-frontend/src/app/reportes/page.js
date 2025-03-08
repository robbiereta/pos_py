'use client'

import { useState, useEffect } from 'react'

export default function Reportes() {
  const [año, setAño] = useState(new Date().getFullYear())
  const [mes, setMes] = useState(new Date().getMonth() + 1)
  const [totales, setTotales] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchTotales = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:5000/api/cortes/totales/${año}/${mes}`)
      const data = await response.json()
      setTotales(data)
    } catch (error) {
      console.error('Error al cargar totales:', error)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchTotales()
  }, [año, mes])

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount || 0)
  }

  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Reportes</h1>

      {/* Selector de fecha */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Año
            </label>
            <select
              value={año}
              onChange={(e) => setAño(parseInt(e.target.value))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              {[2024, 2025, 2026].map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Mes
            </label>
            <select
              value={mes}
              onChange={(e) => setMes(parseInt(e.target.value))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              {meses.map((nombreMes, index) => (
                <option key={index + 1} value={index + 1}>{nombreMes}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Totales del mes */}
      {loading ? (
        <div>Cargando...</div>
      ) : totales ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-blue-100 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">
              Ventas en Efectivo
            </h3>
            <p className="text-2xl font-bold text-blue-900">
              {formatMoney(totales.total_efectivo)}
            </p>
          </div>

          <div className="bg-green-100 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              Ventas con Tarjeta
            </h3>
            <p className="text-2xl font-bold text-green-900">
              {formatMoney(totales.total_tarjeta)}
            </p>
          </div>

          <div className="bg-purple-100 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-2">
              Ventas por Transferencia
            </h3>
            <p className="text-2xl font-bold text-purple-900">
              {formatMoney(totales.total_transferencia)}
            </p>
          </div>

          <div className="bg-gray-100 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Total de Ventas
            </h3>
            <p className="text-2xl font-bold text-gray-900">
              {formatMoney(totales.total_ventas)}
            </p>
          </div>

          <div className="bg-yellow-100 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">
              Retiros
            </h3>
            <p className="text-2xl font-bold text-yellow-900">
              {formatMoney(totales.total_retiros)}
            </p>
          </div>

          <div className="bg-red-100 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-800 mb-2">
              Número de Cortes
            </h3>
            <p className="text-2xl font-bold text-red-900">
              {totales.numero_cortes}
            </p>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500">
          No hay datos disponibles para este período
        </div>
      )}
    </div>
  )
}
