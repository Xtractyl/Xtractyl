import { NavLink } from 'react-router-dom'
import logo from '../assets/xtractyl_dinosaur_with_transparent_background.png'
import { ChevronRight } from 'lucide-react' // falls du Lucide-Icons nutzt

export default function TopBar() {
  return (
    <header className="shadow-md">
      {/* Branding-Zeile */}
      <div className="bg-xtractyl-green text-white px-8 py-3 flex items-center space-x-3">
        <img src={logo} alt="Xtractyl Logo" className="h-8 w-auto" />
        <span className="text-xl font-bold tracking-wide">Xtractyl</span>
      </div>

      {/* Flow-Navigation */}
      <nav className="bg-xtractyl-shadowgreen text-white px-8 py-6 flex items-center justify-center space-x-6">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
        >
          Upload & Convert Docs
        </NavLink>

        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
          to="/project"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
        >
          Create Project
        </NavLink>

        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
          to="/tasks"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
          >
          Upload Tasks
        </NavLink>

        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
            to="/prelabelling"
            className={({ isActive }) =>
                `text-lg px-6 py-3 rounded-xl font-medium transition
                ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
            }
            >
            Start AI
            </NavLink>
        
        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
          to="/review"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
        >
          Review AI
        </NavLink>
        
        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
          to="/results"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
        >
          Get Results
        </NavLink>
        
        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
          to="/evaluate"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
        >
          Evaluate AI
        </NavLink>
        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
        to="/finetune"
        className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
            ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
        }
        >
        Finetune AI
        </NavLink>       
      </nav>
    </header>
  )
}