// src/components/Navigation.jsx
import { Link } from 'react-router-dom';

export default function Navigation() {
  return (
    <nav className="bg-gray-100 p-4 flex gap-4">
      <Link to="/" className="text-blue-600 hover:underline">Home</Link>
      <Link to="/compare" className="text-blue-600 hover:underline">Projektvergleich</Link>
    </nav>
  );
}