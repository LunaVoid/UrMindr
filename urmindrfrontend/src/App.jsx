import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { GoogleAuthProvider } from "firebase/auth";
import Navbar from "./components/Navbar";
import Landing from "./pages/Landing";
import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Calendar from "./pages/Calendar";
import React from "react";
import MyCalendar from "./components/MyCalendar";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(() => {
    return sessionStorage.getItem("accessToken");
  });
  const auth = getAuth();
  

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return () => unsubscribe();
  }, [auth]);

  useEffect(() => {
    if (accessToken) {
      sessionStorage.setItem("accessToken", accessToken);
    }
  }, [accessToken]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <Navbar user={user}/>
      <Routes>
        <Route path="/" element={user ? <Home user={user} accessToken={accessToken} /> : <Landing setAccessToken={setAccessToken} />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/calendar" element={<Calendar accessToken={accessToken}/>} />
      </Routes>
    </Router>
  );
}

export default App;