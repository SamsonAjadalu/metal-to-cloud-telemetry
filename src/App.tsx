import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Dashboard from './pages/LiveDashboard';
import ReplayAnalytics from './pages/ReplayAnalytics';

// CSS is loaded from the public directory via index.html or global link, no need to import here since we copied it to public/stylesheets/app.css

const App: React.FC = () => {
  return (
    <Router>
      <div className="app-container" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <main style={{ flex: 1, paddingTop: '100px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/replay" element={<ReplayAnalytics />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App;
