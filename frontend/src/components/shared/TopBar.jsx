import logo from '../../assets/xtractyl_corporate_without_date_no_bg.png'
import { ChevronRight } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

export default function TopBar() {
  return (
    <header className="shadow-md">
      {/* Branding Line */}
      <div className="bg-xtractyl-green px-8 flex items-center space-x-3 shadow-md hover:brightness-110 transition cursor-pointer">
        <Link to="/aboutpage">
          <img
            src={logo}
            alt="Xtractyl Logo"
            className="h-32 w-auto cursor-pointer"
          />
        </Link>
      </div>

      {/* Navigation (Database Mode only) */}
      <div className="bg-xtractyl-lightgreen text-xtractyl-white px-8 py-4">
        <nav className="bg-xtractyl-lightgreen text-xtractyl-outline/70 px-8 py-6 flex items-center justify-center space-x-6">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Convert Docs
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/project"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Create Labelstudio Project
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/tasks"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Upload in Labelstudio Project
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/prelabelling"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Start AI
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/review"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Review AI
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/results"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Get Results
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/evaluate"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Evaluate AI
          </NavLink>

          <ChevronRight className="text-xtractyl-outline/40 w-5 h-5" />

          <NavLink
            to="/finetune"
            className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-xtractyl-white' : 'hover:bg-xtractyl-offwhite/40'}`            }
          >
            Finetune AI
          </NavLink>
        </nav>
      </div>
    </header>
  )
}