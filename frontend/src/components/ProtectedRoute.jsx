import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to their respective dashboard if they don't have access
    if (user.role === 'admin') {
        return <Navigate to="/admin" replace />;
    } else {
        return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
}
