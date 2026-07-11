import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { ChatProvider } from './context/ChatContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Chat from './pages/Chat'
import About from './pages/About'
import Features from './pages/Features'

function AnimatedRoutes() {
  const location = useLocation()
  const isChat = location.pathname === '/chat'

  return (
    <>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/"         element={<Home />} />
          <Route path="/chat"     element={<Chat />} />
          <Route path="/about"    element={<About />} />
          <Route path="/features" element={<Features />} />
        </Routes>
      </AnimatePresence>
      {/* Hide Footer on full-screen Chat page */}
      {!isChat && <Footer />}
    </>
  )
}

export default function App() {
  return (
    <ChatProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-film-bg text-white font-sans">
          <Navbar />
          <main className="flex-1">
            <AnimatedRoutes />
          </main>
        </div>
      </BrowserRouter>
    </ChatProvider>
  )
}
