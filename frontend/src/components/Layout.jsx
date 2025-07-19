import TopBar from './TopBar'

export default function Layout({ children }) {
    return (
      <div className="flex flex-col min-h-screen">
        <TopBar />
        <main className="flex-1 px-8 py-6 bg-gray-50">
          {children}
        </main>
      </div>
    )
  }