import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for user authentication
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const savedUser = localStorage.getItem('pollUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/login`, { email, password });
      const userData = response.data;
      setUser(userData);
      localStorage.setItem('pollUser', JSON.stringify(userData));
      return userData;
    } catch (error) {
      throw error;
    }
  };

  const register = async (username, email, password) => {
    try {
      const response = await axios.post(`${API}/register`, { username, email, password });
      const userData = response.data;
      setUser(userData);
      localStorage.setItem('pollUser', JSON.stringify(userData));
      return userData;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('pollUser');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login/Register Component
const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData.username, formData.email, formData.password);
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-white mb-2">PollSphere</h2>
          <p className="text-blue-200">Make smart decisions together</p>
        </div>
        
        <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-xl p-8 shadow-2xl">
          <div className="flex mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 rounded-l-lg font-medium transition-colors ${
                isLogin ? 'bg-blue-600 text-white' : 'bg-transparent text-blue-200 hover:bg-blue-600 hover:bg-opacity-20'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 rounded-r-lg font-medium transition-colors ${
                !isLogin ? 'bg-blue-600 text-white' : 'bg-transparent text-blue-200 hover:bg-blue-600 hover:bg-opacity-20'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-4 py-3 bg-white bg-opacity-20 border border-white border-opacity-30 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            )}
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 bg-white bg-opacity-20 border border-white border-opacity-30 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 bg-white bg-opacity-20 border border-white border-opacity-30 rounded-lg text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            
            {error && (
              <div className="text-red-300 text-sm text-center bg-red-900 bg-opacity-30 p-2 rounded">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-transparent transition-all disabled:opacity-50"
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

// Create Poll Component
const CreatePoll = ({ onPollCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  const addOption = () => {
    setOptions([...options, '']);
  };

  const removeOption = (index) => {
    if (options.length > 2) {
      setOptions(options.filter((_, i) => i !== index));
    }
  };

  const updateOption = (index, value) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const pollData = {
        title,
        description,
        options: options.filter(opt => opt.trim() !== ''),
        tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag !== '')
      };

      await axios.post(`${API}/polls?user_id=${user.id}`, pollData);
      
      // Reset form
      setTitle('');
      setDescription('');
      setOptions(['', '']);
      setTags('');
      
      onPollCreated();
    } catch (error) {
      console.error('Error creating poll:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Create New Poll</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Poll title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
        
        <textarea
          placeholder="Poll description..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent h-24 resize-none"
          required
        />
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Options:</label>
          {options.map((option, index) => (
            <div key={index} className="flex mb-2">
              <input
                type="text"
                placeholder={`Option ${index + 1}`}
                value={option}
                onChange={(e) => updateOption(index, e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              {options.length > 2 && (
                <button
                  type="button"
                  onClick={() => removeOption(index)}
                  className="px-3 py-2 bg-red-500 text-white rounded-r-lg hover:bg-red-600"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={addOption}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            + Add Option
          </button>
        </div>
        
        <input
          type="text"
          placeholder="Tags (comma separated)"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all disabled:opacity-50"
        >
          {loading ? 'Creating...' : 'Create Poll (+20 XP)'}
        </button>
      </form>
    </div>
  );
};

// Poll Card Component
const PollCard = ({ poll, onVote }) => {
  const [selectedOption, setSelectedOption] = useState('');
  const [voting, setVoting] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    // Check if user has already voted
    const userVoted = poll.options.some(option => 
      option.voter_ids.includes(user.id)
    );
    setHasVoted(userVoted);
  }, [poll, user]);

  const handleVote = async () => {
    if (!selectedOption || voting || hasVoted) return;
    
    setVoting(true);
    try {
      await axios.post(`${API}/vote`, {
        poll_id: poll.id,
        option_id: selectedOption,
        user_id: user.id
      });
      
      setHasVoted(true);
      onVote();
    } catch (error) {
      console.error('Error voting:', error);
    } finally {
      setVoting(false);
    }
  };

  const getPercentage = (votes) => {
    return poll.total_votes > 0 ? ((votes / poll.total_votes) * 100).toFixed(1) : 0;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-6 hover:shadow-xl transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">{poll.title}</h3>
          <p className="text-gray-600 mb-3">{poll.description}</p>
          <div className="flex items-center text-sm text-gray-500 space-x-4">
            <span>By @{poll.creator_username}</span>
            <span>{poll.total_votes} votes</span>
            <span>{new Date(poll.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
      
      {poll.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {poll.tags.map((tag, index) => (
            <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
              #{tag}
            </span>
          ))}
        </div>
      )}
      
      <div className="space-y-3">
        {poll.options.map((option) => (
          <div key={option.id} className="relative">
            {hasVoted ? (
              <div className="border-2 border-gray-200 rounded-lg p-3 relative overflow-hidden">
                <div 
                  className="absolute left-0 top-0 h-full bg-blue-100 transition-all duration-500"
                  style={{ width: `${getPercentage(option.votes)}%` }}
                />
                <div className="relative flex justify-between items-center">
                  <span className="font-medium">{option.text}</span>
                  <span className="text-sm font-bold text-blue-600">
                    {option.votes} votes ({getPercentage(option.votes)}%)
                  </span>
                </div>
              </div>
            ) : (
              <label className="flex items-center p-3 border-2 border-gray-200 rounded-lg hover:border-blue-300 cursor-pointer transition-colors">
                <input
                  type="radio"
                  name={`poll-${poll.id}`}
                  value={option.id}
                  checked={selectedOption === option.id}
                  onChange={(e) => setSelectedOption(e.target.value)}
                  className="mr-3 text-blue-600"
                />
                <span className="font-medium">{option.text}</span>
              </label>
            )}
          </div>
        ))}
      </div>
      
      {!hasVoted && (
        <button
          onClick={handleVote}
          disabled={!selectedOption || voting}
          className="mt-4 w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-medium py-3 px-4 rounded-lg hover:from-green-600 hover:to-blue-600 focus:outline-none focus:ring-2 focus:ring-green-500 transition-all disabled:opacity-50"
        >
          {voting ? 'Voting...' : 'Vote (+5 XP)'}
        </button>
      )}
      
      {hasVoted && (
        <div className="mt-4 text-center text-green-600 font-medium">
          ✓ You have voted on this poll
        </div>
      )}
    </div>
  );
};

// Leaderboard Component
const Leaderboard = () => {
  const [leaders, setLeaders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get(`${API}/leaderboard`);
      setLeaders(response.data);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading leaderboard...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        🏆 Leaderboard
      </h2>
      
      <div className="space-y-3">
        {leaders.map((leader, index) => (
          <div key={leader.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                index === 0 ? 'bg-yellow-400 text-yellow-900' :
                index === 1 ? 'bg-gray-400 text-gray-900' :
                index === 2 ? 'bg-orange-400 text-orange-900' :
                'bg-blue-100 text-blue-900'
              }`}>
                {index + 1}
              </div>
              <div>
                <div className="font-bold text-gray-800">@{leader.username}</div>
                <div className="text-sm text-gray-600">
                  {leader.total_polls_created} polls • {leader.total_votes_cast} votes
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">{leader.xp}</div>
              <div className="text-sm text-gray-500">XP</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreatePoll, setShowCreatePoll] = useState(false);
  const [activeTab, setActiveTab] = useState('polls');
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchPolls();
  }, []);

  const fetchPolls = async () => {
    try {
      const response = await axios.get(`${API}/polls`);
      setPolls(response.data);
    } catch (error) {
      console.error('Error fetching polls:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePollCreated = () => {
    setShowCreatePoll(false);
    fetchPolls();
  };

  const handleVote = () => {
    fetchPolls();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                PollSphere
              </h1>
              <div className="hidden sm:flex items-center space-x-6">
                <button
                  onClick={() => setActiveTab('polls')}
                  className={`px-3 py-2 rounded-md font-medium ${
                    activeTab === 'polls' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Polls
                </button>
                <button
                  onClick={() => setActiveTab('leaderboard')}
                  className={`px-3 py-2 rounded-md font-medium ${
                    activeTab === 'leaderboard' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Leaderboard
                </button>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">@{user.username}</span>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full font-bold">
                  {user.xp} XP
                </span>
              </div>
              <button
                onClick={() => setShowCreatePoll(!showCreatePoll)}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 font-medium"
              >
                Create Poll
              </button>
              <button
                onClick={logout}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {showCreatePoll && (
          <CreatePoll onPollCreated={handlePollCreated} />
        )}
        
        {activeTab === 'polls' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Latest Polls</h2>
              <div className="text-sm text-gray-600">
                {polls.length} active polls
              </div>
            </div>
            
            {loading ? (
              <div className="text-center py-8">Loading polls...</div>
            ) : polls.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600 mb-4">No polls yet!</p>
                <button
                  onClick={() => setShowCreatePoll(true)}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 font-medium"
                >
                  Create the First Poll
                </button>
              </div>
            ) : (
              <div>
                {polls.map((poll) => (
                  <PollCard 
                    key={poll.id} 
                    poll={poll} 
                    onVote={handleVote}
                  />
                ))}
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'leaderboard' && <Leaderboard />}
      </main>
    </div>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return user ? <Dashboard /> : <AuthForm />;
}

// App with Context Provider
function AppWithProviders() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithProviders;