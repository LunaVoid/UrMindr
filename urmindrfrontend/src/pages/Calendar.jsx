import React from "react";
import MyCalendar from "../components/MyCalendar";

function Calendar({ accessToken }) {
  return (
    <div>
      <MyCalendar token={accessToken} />
    </div>
  );
}

export default Calendar;
