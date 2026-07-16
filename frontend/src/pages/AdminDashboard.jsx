import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Film, CheckCircle, Database, Upload, Trash2, RefreshCw } from 'lucide-react';
import axios from 'axios';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  
  const [stats, setStats] = useState({ users: 0, movies: 0, pending_requests: 0, chat_calls: 0 });
  const [movies, setMovies] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [ingestMessage, setIngestMessage] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, moviesRes, reqsRes] = await Promise.all([
        axios.get('/api/admin/stats'),
        axios.get('/api/admin/movies'),
        axios.get('/api/admin/requests')
      ]);
      setStats(statsRes.data);
      setMovies(moviesRes.data);
      setRequests(reqsRes.data);
    } catch (err) {
      console.error("Failed to fetch admin data", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (id) => {
    try {
        await axios.post(`/api/admin/requests/${id}/approve`);
        fetchData();
    } catch(err) { console.error(err); }
  };

  const handleReject = async (id) => {
    try {
        await axios.post(`/api/admin/requests/${id}/reject`);
        fetchData();
    } catch(err) { console.error(err); }
  };

  const handleDeleteMovie = async (title) => {
      if(!window.confirm(`Are you sure you want to delete ${title}?`)) return;
      try {
          await axios.delete(`/api/admin/movies/${encodeURIComponent(title)}`);
          fetchData();
      } catch(err) { console.error(err); }
  };

  const handleReingest = async (title) => {
      try {
          await axios.post(`/api/admin/movies/${encodeURIComponent(title)}/reingest`);
          fetchData();
      } catch(err) { console.error(err); }
  };

  const handleTriggerIngestion = async () => {
      try {
          const res = await axios.post('/api/admin/ingest');
          setIngestMessage(res.data.message);
          setTimeout(() => setIngestMessage(''), 3000);
      } catch(err) {
          setIngestMessage('Failed to trigger ingestion');
      }
  };

  const handleFileUpload = async (e) => {
      e.preventDefault();
      if(!file) return;
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
          setUploadMessage('Uploading...');
          await axios.post('/api/upload', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
          });
          setUploadMessage('Uploaded successfully! Trigger ingestion to process it.');
          setFile(null);
      } catch(err) {
          setUploadMessage(err.response?.data?.detail || 'Upload failed');
      }
  };

  const handleRequestFileUpload = async (e, reqId) => {
      const selectedFile = e.target.files[0];
      if(!selectedFile) return;
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('request_id', reqId);
      
      try {
          await axios.post('/api/upload', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
          });
          alert('Screenplay uploaded and fulfilled successfully! Ingestion is running in the background.');
          fetchData();
      } catch(err) {
          alert('Failed to upload screenplay for request.');
      }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl flex gap-8">
      
      {/* Sidebar */}
      <div className="w-64 shrink-0">
        <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-film-card p-6 rounded-2xl border border-gray-800 sticky top-24"
        >
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                <Database className="text-film-accent" size={20} />
                Admin Panel
            </h2>
            <nav className="flex flex-col gap-2">
                {[
                    { id: 'overview', label: 'Overview', icon: CheckCircle },
                    { id: 'movies', label: 'Movies & Scripts', icon: Film },
                    { id: 'ingestion', label: 'Ingestion Engine', icon: RefreshCw },
                    { id: 'requests', label: 'User Requests', icon: Users },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                            activeTab === tab.id 
                            ? 'bg-film-accent/20 text-film-accent border border-film-accent/30' 
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'
                        }`}
                    >
                        <tab.icon size={16} />
                        {tab.label}
                    </button>
                ))}
            </nav>
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="flex-1">
        <AnimatePresence mode="wait">
            <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="bg-film-card p-8 rounded-2xl border border-gray-800 min-h-[70vh]"
            >
                {/* OVERVIEW TAB */}
                {activeTab === 'overview' && (
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-8">Dashboard Overview</h1>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <StatCard title="Total Users" value={stats.users} icon={Users} color="text-blue-500" />
                            <StatCard title="Processed Movies" value={stats.movies} icon={Film} color="text-green-500" />
                            <StatCard title="Pending Requests" value={stats.pending_requests} icon={CheckCircle} color="text-yellow-500" />
                            <StatCard title="Chatbot Queries" value={stats.chat_calls} icon={Database} color="text-purple-500" />
                        </div>
                    </div>
                )}

                {/* MOVIES TAB */}
                {activeTab === 'movies' && (
                    <div>
                        <div className="flex justify-between items-center mb-6">
                            <h1 className="text-3xl font-bold text-white">Ingested Movies</h1>
                            <button onClick={fetchData} className="text-sm text-gray-400 hover:text-white flex items-center gap-2">
                                <RefreshCw size={14} /> Refresh
                            </button>
                        </div>
                        {loading ? <p className="text-gray-500">Loading...</p> : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-gray-800 text-gray-400 text-sm">
                                            <th className="pb-3 font-medium">Title</th>
                                            <th className="pb-3 font-medium">Processed Date</th>
                                            <th className="pb-3 font-medium text-center">Chunks</th>
                                            <th className="pb-3 font-medium text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {movies.map((m, i) => (
                                            <tr key={i} className="border-b border-gray-800/50 hover:bg-white/5 transition-colors">
                                                <td className="py-4 text-white font-medium">{m.title}</td>
                                                <td className="py-4 text-gray-400 text-sm">{new Date(m.processed_at).toLocaleDateString()}</td>
                                                <td className="py-4 text-gray-400 text-sm text-center">{m.chunks_stored}</td>
                                                <td className="py-4 text-right space-x-2">
                                                    <button onClick={() => handleReingest(m.title)} className="px-3 py-1 bg-blue-500/10 text-blue-500 rounded-lg text-xs font-bold hover:bg-blue-500/20">Re-Ingest</button>
                                                    <button onClick={() => handleDeleteMovie(m.title)} className="px-3 py-1 bg-red-500/10 text-red-500 rounded-lg text-xs font-bold hover:bg-red-500/20">Delete</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {movies.length === 0 && <p className="text-gray-500 mt-4 text-center">No movies processed yet.</p>}
                            </div>
                        )}
                    </div>
                )}

                {/* INGESTION TAB */}
                {activeTab === 'ingestion' && (
                    <div className="space-y-12">
                        <div>
                            <h1 className="text-3xl font-bold text-white mb-2">Ingestion Engine</h1>
                            <p className="text-gray-400 mb-8">Upload PDFs or trigger the processing pipeline for pending files.</p>
                            
                            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-bold text-white mb-1">Trigger Pipeline</h3>
                                    <p className="text-sm text-gray-400">Scans for new or marked-for-reingestion PDFs and processes them.</p>
                                </div>
                                <button 
                                    onClick={handleTriggerIngestion}
                                    className="bg-film-accent text-white px-6 py-2 rounded-lg font-medium hover:bg-film-accent/90 transition-colors flex items-center gap-2"
                                >
                                    <Database size={18} />
                                    Run Ingestion
                                </button>
                            </div>
                            {ingestMessage && <p className="mt-3 text-sm text-green-400">{ingestMessage}</p>}
                        </div>

                        <div>
                            <h3 className="text-xl font-bold text-white mb-4">Upload New Screenplay</h3>
                            <form onSubmit={handleFileUpload} className="bg-gray-900 p-6 rounded-xl border border-gray-800 border-dashed flex flex-col items-center justify-center gap-4">
                                <Upload size={32} className="text-gray-500" />
                                <input 
                                    type="file" 
                                    accept=".pdf" 
                                    onChange={(e) => setFile(e.target.files[0])}
                                    className="text-gray-400 text-sm file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-film-accent/20 file:text-film-accent hover:file:bg-film-accent/30"
                                />
                                <button type="submit" disabled={!file} className="bg-white text-black px-6 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors disabled:opacity-50">
                                    Upload PDF
                                </button>
                            </form>
                            {uploadMessage && <p className="mt-3 text-sm text-gray-400 text-center">{uploadMessage}</p>}
                        </div>
                    </div>
                )}

                {/* REQUESTS TAB */}
                {activeTab === 'requests' && (
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-8">User Movie Requests</h1>
                        {loading ? <p className="text-gray-500">Loading...</p> : (
                            <div className="space-y-4">
                                {requests.map(req => (
                                    <div key={req.id} className="bg-gray-900 p-5 rounded-xl border border-gray-800 flex justify-between items-center">
                                        <div>
                                            <h3 className="text-lg font-bold text-white">{req.title}</h3>
                                            <p className="text-sm text-gray-400">Requested by: <span className="text-gray-300">{req.username}</span> on {new Date(req.created_at).toLocaleDateString()}</p>
                                        </div>
                                        
                                        {req.status === 'pending' ? (
                                            <div className="flex gap-2">
                                                <button onClick={() => handleApprove(req.id)} className="px-4 py-2 bg-green-500/10 text-green-500 rounded-lg text-sm font-bold hover:bg-green-500/20">Approve</button>
                                                <button onClick={() => handleReject(req.id)} className="px-4 py-2 bg-red-500/10 text-red-500 rounded-lg text-sm font-bold hover:bg-red-500/20">Reject</button>
                                            </div>
                                        ) : req.status === 'approved' ? (
                                            <div className="flex items-center gap-4">
                                                <span className="px-3 py-1 rounded-full text-xs font-bold bg-green-500/10 text-green-500">
                                                    APPROVED
                                                </span>
                                                <label className="cursor-pointer flex items-center gap-2 px-4 py-2 bg-film-accent text-white rounded-lg text-sm font-bold hover:bg-film-accent/90 transition-colors">
                                                    <Upload size={14} />
                                                    Upload PDF
                                                    <input 
                                                        type="file" 
                                                        accept=".pdf" 
                                                        className="hidden" 
                                                        onChange={(e) => handleRequestFileUpload(e, req.id)}
                                                    />
                                                </label>
                                            </div>
                                        ) : (
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                                                req.status === 'fulfilled' ? 'bg-blue-500/10 text-blue-500' : 'bg-red-500/10 text-red-500'
                                            }`}>
                                                {req.status.toUpperCase()}
                                            </span>
                                        )}
                                    </div>
                                ))}
                                {requests.length === 0 && <p className="text-gray-500">No requests found.</p>}
                            </div>
                        )}
                    </div>
                )}
            </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color }) {
    return (
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
                <Icon size={20} className={color} />
            </div>
            <p className="text-3xl text-white font-bold">{value}</p>
        </div>
    );
}
