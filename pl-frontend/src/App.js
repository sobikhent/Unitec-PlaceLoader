import React, { useRef, useState } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';
import './App.css'; // Importing CSS
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('');
  const [tableData, setTableData] = useState(null);
  const tableRef = useRef(null);  // Create a ref
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    setTableData(null);
    setIsLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/process_data', {
        keyword,
        city,
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const parsedData = JSON.parse(response.data);
      setTableData(parsedData);
      setIsLoading(false);
    } catch (error) {
      console.error('There was an error!', error);
      setIsLoading(false);
    }
  };

  const exportToExcel = () => {
    const currentTime = new Date();
    const formattedTime = `${currentTime.getFullYear()}-${currentTime.getMonth()+1}-${currentTime.getDate()}_${currentTime.getHours()}-${currentTime.getMinutes()}-${currentTime.getSeconds()}`;
    const fileName = `${city}_${keyword}_${formattedTime}.xlsx`;
    
    const wb = XLSX.utils.table_to_book(tableRef.current);
    XLSX.writeFile(wb, fileName);
  };
  

  return (
    <div className="App d-flex flex-column align-items-center justify-content-center">
      <div className="form-wrapper text-center col-md-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="keyword" className="form-label">Enter your special place</label>
            <br></br>
            <input
              type="text"
              className="form-control rounded"
              placeholder="Keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              disabled={isLoading}  // Disable input when loading
            />
          </div>
          <div className="mb-3">
            <label htmlFor="city" className="form-label">Enter City name</label>
            <br></br>
            <input
              type="text"
              className="form-control rounded"
              placeholder="City"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              disabled={isLoading}  // Disable input when loading
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary btn-rounded search-button" 
            disabled={isLoading}  // Disable button when loading
          >
            {isLoading ? "Fetching Data" : "Search"}
          </button>
        </form>
    </div>

      {isLoading && <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>}

      {tableData && !isLoading && (
        <div className='table-wrapper'>
          <div className="result-container">
            <div className="table-container">
              <table ref={tableRef} className="table table-bordered">
                <thead>
                  <tr>
                    {tableData.columns.map((col, index) => (
                      <th key={index}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableData.data.map((row, index) => (
                    <tr key={index}>
                      {row.map((cell, i) => (
                        <td key={i}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="export-button-container">
              <button onClick={exportToExcel} className="btn btn-success export-button">Export to Excel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
