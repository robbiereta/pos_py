// API utility functions to connect with your backend

const API_BASE_URL = 'http://localhost:5003/api';

// Fetch sales data from backend
export const fetchSalesData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/sales/`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching sales data:', error);
    throw error;
  }
};

// Generate CFDI for a specific sale
export const generateCFDI = async (notaVenta) => {
  try {
    const response = await fetch(`${API_BASE_URL}/generate_client_cfdi`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ nota_venta: notaVenta }),
    });
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error generating CFDI:', error);
    throw error;
  }
};
