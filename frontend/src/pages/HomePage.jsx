import { useState } from 'react';
import Header from '../components/Header';
import HeroSection from '../components/Herosection';
import Footer from '../components/Footer';
import { LoginModal } from '../components/Loginmodal';
import { RegisterModal } from '../components/Registermodal';

const HomePage = () => {
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
};

export default HomePage;