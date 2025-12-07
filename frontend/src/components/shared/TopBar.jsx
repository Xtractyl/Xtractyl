import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import logo from '../../assets/xtractyl_dinosaur_with_transparent_background.png'
import { ChevronRight } from 'lucide-react' 

export default function TopBar() {
  const [activeFlow, setActiveFlow] = useState('database')

  useEffect(() => {
    const saved = localStorage.getItem('activeFlow')
    if (saved === 'database' || saved === 'singlequestion') setActiveFlow(saved)
  }, [])

  const selectFlow = (flow) => {
    setActiveFlow(flow)
    localStorage.setItem('activeFlow', flow)
  }
  return (
    <header className="shadow-md">
      {/* Branding Line */}
<div className="bg-gradient-to-r from-xtractyl-offwhite to-white text-xtractyl-orange px-8 py-3 flex items-center space-x-3 shadow-md">        <img src={logo} alt="Xtractyl Logo" className="h-20 w-auto" />
 <span
  className="text-4xl font-bold tracking-wide antialiased"
  style={{ textShadow: '0 1px 2px rgba(0,0,0,0.25)' }}
>
  Xtractyl
</span>
      </div>

      {/* switch between workflows */}
      <div className="bg-xtractyl-shadowgreen text-white px-8 py-4">
 
        {/* buttons for workflow selection */}
       <div className="flex justify-center items-center space-x-4 mb-4">
          <button
            type="button"
            aria-pressed={activeFlow === 'database'}
            onClick={() => selectFlow('database')}
            className={`px-3 py-1 rounded text-sm transition
              ${activeFlow === 'database'
                ? 'bg-xtractyl-green'
                : 'bg-xtractyl-green/50 hover:bg-xtractyl-green/70'}`}
          >
            Database Mode
          </button>
          <button
            type="button"
            aria-pressed={activeFlow === 'singlequestion'}
            onClick={() => selectFlow('singlequestion')}
            className={`px-3 py-1 rounded text-sm transition
              ${activeFlow === 'singlequestion'
                ? 'bg-xtractyl-green'
                : 'bg-xtractyl-green/50 hover:bg-xtractyl-green/70'}`}
          >
            Single Question Mode
          </button>
        </div>

        {/* Conditional Navigation */}
        {activeFlow === 'database' ? (
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
          Create Project Files and Labelstudio Project
        </NavLink>

        <ChevronRight className="text-white w-5 h-5" />

        <NavLink
          to="/tasks"
          className={({ isActive }) =>
            `text-lg px-6 py-3 rounded-xl font-medium transition
             ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`
          }
          >
          Upload Tasks in Labelstudio Project
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
        ) : (
          <nav className="bg-xtractyl-shadowgreen text-white px-8 py-6 flex items-center justify-center space-x-6">
            <NavLink to="/library" className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
              ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`}>PDF library</NavLink>
            <ChevronRight className="text-white w-5 h-5" />
            <NavLink to="/question" className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
              ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`}>Ask Question</NavLink>
            <ChevronRight className="text-white w-5 h-5" />
            <NavLink to="/uploadanswer" className={({ isActive }) =>
              `text-lg px-6 py-3 rounded-xl font-medium transition
              ${isActive ? 'bg-xtractyl-green text-white' : 'hover:bg-xtractyl-green/80'}`}>Review and Upload Answer</NavLink>
          </nav>
        )}

    </div>
    </header>
  )
}