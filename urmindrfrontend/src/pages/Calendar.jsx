import {useEffect, useState} from "react";

function Calendar( {token}) {
    const [events, setEvents] = useState([]);


    useEffect(() => {
        if (!token) return;

        fetch("https://www.googleapis.com/calendar/v3/calendars/primary/events", {
        headers: { Authorization: `Bearer ${token}` },
        })
        .then(res => res.json())
        .then(data => setEvents(data.items || []))
        .catch(err => console.error(err));
        }, [token]);


        return (
    <div>
      <h1>My Calendar</h1>
        <ul>
            {events.map((event) => (
            <li key={event.id}>
                {event.summary} - {event.start.dateTime || event.start.date}
            </li>
            ))}
        </ul>
        <button onClick={handleConnectCalendar} className="bg-green-500 text-white px-4 py-2 rounded">
          Connect Google Calendar
        </button>

    </div>
  );
}

export default Calendar;