import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import styles from '../styles/Home.module.css';

// This would connect to your backend API
import { fetchSalesData, generateCFDI } from '../utils/api';

const Sales = () => {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const loadSales = async () => {
      try {
        const data = await fetchSalesData();
        setSales(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching sales data:', error);
        setLoading(false);
      }
    };
    
    loadSales();
  }, []);

  const handleGenerateCFDI = async (saleId) => {
    try {
      const result = await generateCFDI(saleId);
      if (result.success) {
        setMessage(`Factura generada exitosamente para venta ${saleId}`);
        // Refresh sales data to show updated status
        const updatedData = await fetchSalesData();
        setSales(updatedData);
      } else {
        setMessage(`Error al generar factura: ${result.error}`);
      }
    } catch (error) {
      setMessage(`Error al generar factura: ${error.message}`);
    }
  };

  if (loading) {
    return <div className={styles.container}>Loading...</div>;
  }

  return (
    <div className={styles.container}>
      <Head>
        <title>POS - Sales</title>
        <meta name="description" content="Sales management for POS system" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Sales Management
        </h1>
        
        {message && (
          <div className={styles.alert}>
            {message}
          </div>
        )}

        <div className={styles.grid}>
          {sales.length > 0 ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Customer</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sales.map(sale => (
                  <tr key={sale._id}>
                    <td>{sale._id}</td>
                    <td>{sale.date || 'N/A'}</td>
                    <td>{sale.client_id || 'N/A'}</td>
                    <td>${sale.total_amount}</td>
                    <td>{sale.facturada ? 'Facturada' : 'Pendiente'}</td>
                    <td>
                      <button>View Details</button>
                      {!sale.facturada && (
                        <button onClick={() => handleGenerateCFDI(sale._id)}>
                          Generar Factura
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No sales data available.</p>
          )}
        </div>
        
        <div className={styles.card}>
          <button>Create New Sale</button>
        </div>
      </main>
    </div>
  );
};

export default Sales;
