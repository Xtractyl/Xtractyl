import { NavLink } from 'react-router-dom'

export default function TopBar() {
  return (
    <nav className="bg-gray-800 text-white px-6 py-4 flex space-x-6">
      <NavLink
        to="/"
        className={({ isActive }) =>
          isActive ? "font-bold underline" : "hover:underline"
        }
      >
        Upload
      </NavLink>
      <NavLink
        to="/status"
        className={({ isActive }) =>
          isActive ? "font-bold underline" : "hover:underline"
        }
      >
        Status
      </NavLink>
    </nav>
  )
}