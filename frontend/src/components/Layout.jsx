import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto px-3 py-4 md:px-4 md:py-8">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
