import { useState } from 'react';
import './App.css';
import './index.css';
import Footer from './components/Footer';
import Header from './components/Header';
import HeroSection from './components/Herosection';
import { LoginModal } from './components/LoginModal';
import { RegisterModal } from './components/RegisterModal';

function App() {
  const [modal, setModal] = useState(null); // null | 'login' | 'register'

  return (
    <>
      <Header onOpenLogin={() => setModal('login')} />
      <HeroSection />
      <Footer />



      <LoginModal
        isOpen={modal === 'login'}
        onClose={() => setModal(null)}
        onSwitchToRegister={() => setModal('register')}
      />

      <RegisterModal
        isOpen={modal === 'register'}
        onClose={() => setModal(null)}
        onSwitchToLogin={() => setModal('login')}
      />
    </>
  );
}

export default App;