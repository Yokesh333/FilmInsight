import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { ChatProvider } from './context/ChatContext'
import { AuthProvider } from './context/AuthContext'
import { MovieProvider } from './context/MovieContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Chat from './pages/Chat'
import About from './pages/About'
import Features from './pages/Features'
import Login from './pages/Login'
import Register from './pages/Register'
import UserDashboard from './pages/UserDashboard'
import AdminDashboard from './pages/AdminDashboard'

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
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
        </Routes>
      </AnimatePresence>
      {/* Hide Footer on full-screen Chat page */}
      {!isChat && <Footer />}
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <MovieProvider>
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
      </MovieProvider>
    </AuthProvider>
  )
}
