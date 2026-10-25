import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import Layout from './components/layout/Layout';
import Overview from './pages/Overview';
import Services from './pages/Services';
import ServiceDetail from './pages/ServiceDetail';
import Anomalies from './pages/Anomalies';
import Alerts from './pages/Alerts';
import Incidents from './pages/Incidents';
import Settings from './pages/Settings';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><BrowserRouter><Routes><Route element={<Layout />}>
    <Route path="/" element={<Overview />} />
    <Route path="/services" element={<Services />} />
    <Route path="/services/:id" element={<ServiceDetail />} />
    <Route path="/anomalies" element={<Anomalies />} />
    <Route path="/alerts" element={<Alerts />} />
    <Route path="/incidents" element={<Incidents />} />
    <Route path="/settings" element={<Settings />} />
    <Route path="*" element={<div className="p-8 text-slate-400">Page not found.</div>} />
  </Route></Routes></BrowserRouter></React.StrictMode>
);
