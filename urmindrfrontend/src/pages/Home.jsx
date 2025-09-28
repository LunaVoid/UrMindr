import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import { getFirestore, collection, query, orderBy, limit, where, getDocs, doc, getDoc, updateDoc, setDoc, serverTimestamp } from "firebase/firestore";
import React from 'react';
import '../progressBar.css';

function Home({ user, accessToken }) {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [percentCompleted, setpercentCompleted] = useState(0);

  //console.log(user)
  console.log("Auth user ID:", user.uid);
  console.log("Document ID should match this");
  useEffect(()=>{

    console.log("Auth user ID:", user.uid);
    console.log("Document ID should match this");
    const updateLoginStreak = async (userId) => {
    const db = getFirestore();
    const userDocRef = doc(db, 'users', userId);
    
    try {
      const userDoc = await getDoc(userDocRef);
      
      if (userDoc.exists()) {
        const userData = userDoc.data();
        
        // Check if loginStreak field exists
        if (!userData.loginStreak) {
          // First time - create the field
          await updateDoc(userDocRef, {
            'loginStreak.currentStreak': 1,
            'loginStreak.longestStreak': 1,
            'loginStreak.lastLoginDate': serverTimestamp()
          });
          console.log("Created login streak for new user");
          setpercentCompleted(1);
          return;
        }

        // User has existing streak data
        const lastLogin = userData.loginStreak.lastLoginDate?.toDate();
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        
        if (lastLogin) {
          const lastLoginDate = new Date(lastLogin.getFullYear(), lastLogin.getMonth(), lastLogin.getDate());
          const yesterday = new Date(today);
          yesterday.setDate(yesterday.getDate() - 1);
          
          if (lastLoginDate.getTime() === today.getTime()) {
            // Already logged in today
            setpercentCompleted(10);
            return;
          } else if (lastLoginDate.getTime() === yesterday.getTime()) {
            // Consecutive day - increment streak
            const newStreak = userData.loginStreak.currentStreak + 1;
            const longestStreak = Math.max(newStreak, userData.loginStreak.longestStreak);
            setpercentCompleted(newStreak);
            await updateDoc(userDocRef, {
              'loginStreak.currentStreak': newStreak,
              'loginStreak.longestStreak': longestStreak,
              'loginStreak.lastLoginDate': serverTimestamp()
            });
            console.log(`Streak continued: ${newStreak} days`);
          } else {
            // Streak broken - reset to 1
            await updateDoc(userDocRef, {
              'loginStreak.currentStreak': 1,
              'loginStreak.lastLoginDate': serverTimestamp()
            });
            console.log("Streak reset to 1");
          }
        }
        
      } 
      else {
        // User document doesn't exist - create it
        await setDoc(userDocRef, {
          userId: userId,
          loginStreak: {
            currentStreak: 1,
            longestStreak: 1,
            lastLoginDate: serverTimestamp()
          }
        });
      }
    } 
    catch (error) {
      console.error("Error updating streak:", error);
    }
  };

  updateLoginStreak(user.uid)
  }, [])


 const calculateProgress = (completedTasks, totalTasks) => {
  if (totalTasks === 0) return 0;
  return Math.round((completedTasks / totalTasks) * 100);
};

const ProgressBar = () => {
  return (
    <div className="flex flex-col items-center w-full max-w-xl">
      <progress
        className="progressBar w-full h-5"
        value={percentCompleted}
        max={100}
      />
      <p className="mt-2 mb-5 text-xl">
         {percentCompleted} days of 100 day streak!
      </p>
    </div>
  );
};
  
  useEffect(() => {
    const fetchEvents = async () => {
      if (!accessToken) {
        return; // Do not fetch if accessToken is not available
      }

      try {
        const timeMin = new Date().toISOString();
        const response = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=15&orderBy=startTime&singleEvents=true&timeMin=${timeMin}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          console.error("Error fetching events:", errorData);
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setEvents(data.items);
      } catch (error) {
        setError("Failed to fetch calendar events.");
      }
    };

    fetchEvents();
  }, [accessToken]);

  const handleAddEvent = async (e) => {
    e.preventDefault();
    if (!accessToken) {
      setError("Not authenticated to add event.");
      return;
    }

    const event = {
      summary: summary,
      start: {
        dateTime: new Date(startTime).toISOString(),
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      end: {
        dateTime: new Date(endTime).toISOString(),
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
    };

    try {
      const response = await fetch(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(event),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error creating event:", errorData);
        throw new Error("Failed to create event");
      }

      // Refresh events list after adding a new one
      // A simple way is to re-fetch, but for better UX you might just add the new event to the state
      alert("Event created successfully!");
      setSummary("");
      setStartTime("");
      setEndTime("");
      // Re-fetch events to show the new one
      // Note: This is a simple approach. For a more optimized UX, you could add the new event directly to the events state.
      const timeMin = new Date().toISOString();
      const eventsResponse = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=15&orderBy=startTime&singleEvents=true&timeMin=${timeMin}`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
      print(accessToken);
      const data = await eventsResponse.json();
      setEvents(data.items);
    } catch (error) {
      setError(error.message);
    }
  };

  const displayEvents = (events) => {
    console.log(events)
    if (error) {
      return <p className="text-red-500">{error}</p>;
    }
    if (!events || events.length === 0) {
      return <p>No upcoming events found.</p>;
    } else {
      return (
        <ul className="text-left">
          {events.map((event, index) => {
            const start = event.start.dateTime || event.start.date;
            return (
              <li key={index}>

                {new Date(start).toLocaleString()} - {event.summary}
              </li>
              
            );
          })}
        </ul>
      );
    }
  };


  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="text-center w-full max-w-2xl">
        
        <h1 className="text-4xl font-bold mb-4">Welcome, {user.displayName} to The Command Center!</h1>
        <div className="flex justify-center pt-5">
            <ProgressBar />
        </div>
        {/* <p className="text-lg mb-8">Email: {user.email}</p>*/}
        <div className="flex flex-row items-center justify-evenly pb-5">
          <Link to="/calendar">
            <button className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mb-6">
              Go to Calendar
            </button>
          </Link>
          <Link to="/chat">
            <button className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mb-6">
              Go to Chat
            </button>
          </Link>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-2xl font-bold mb-4">Create New Task</h2>
          <form onSubmit={handleAddEvent} className="flex flex-col gap-4">
            <input
              type="text"
              placeholder="Event Title"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="p-2 border rounded"
              required
            />
            <div className="flex gap-4">
              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="p-2 border rounded w-full"
                required
              />
              <input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="p-2 border rounded w-full"
                required
              />
            </div>
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              Add Task
            </button>
          </form>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Upcoming Tasks</h2>
          {displayEvents(events)}

          
        </div>
      </div>
    </div>
  );
}

export default Home;
