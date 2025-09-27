import { useEffect, useState } from "react";

function Home({ user }) {

    const [events, setEvents] = useState([]);

    useEffect(() => {
      const fetchEvents = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/cal/events", {
          credentials: "include", // <-- important to include cookies/session
        });

        if (!response.ok) {
          if (response.status === 401) {
            window.location.href = "http://localhost:5000/api/cal/authorize"; // redirect to OAuth
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Fetched events:", data.events);
        setEvents(data.events);
      } catch (error) {
        console.error("Error fetching events:", error);
      }
    };
      fetchEvents();

      }, []);

  const displayEvents = (events) => {
    if (!events || events.length === 0) {
      return <p>No upcoming events found.</p>;
    } else {
      return (
        <ul>
          {events.map((event, index) => {
            const start = event.start.dateTime || event.start.date;
            return (
              <li key={index}>
                {start} - {event.summary}
              </li>
            );
          })}
        </ul>
      );
    };
  }

  return (

    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Account Information</h1>
        <p className="text-lg">Welcome, {user.displayName}!</p>
        <p className="text-lg">Email: {user.email}</p>
        <p className="text-lg mb-8">Calendar</p>
          {displayEvents(events)}
      </div>
    </div>
  );
}


export default Home;
