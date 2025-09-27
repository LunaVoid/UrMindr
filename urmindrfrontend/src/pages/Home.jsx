import { useEffect, useState } from "react";

function Home({ user, accessToken }) {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);

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
          // Log the error response for more details
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
