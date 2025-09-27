import React from 'react'
import { useState, useEffect } from "react";
import { getAuth, onAuthStateChanged } from "firebase/auth";


function Chat() {

    const [started, setStarted] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [user, setUser] = useState(null);

    useEffect(() => {
        const auth = getAuth();
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
        });
        return () => unsubscribe();
    }, []);

    const sendMessageToApi = async (message) => {
        if (!user) {
            console.error("No user logged in.");
            setMessages(prevMessages => [...prevMessages, { text: "You must be logged in to use the chat.", sender: 'bot' }]);
            return;
        }

        const idToken = await user.getIdToken();
        const url = "http://127.0.0.1:5000/api/toolcall";
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${idToken}`
                },
                body: JSON.stringify({ prompt: message })
            });
            
            const result = await response.json();

            if (!response.ok) {
                // Handle API errors (e.g., 401, 500 from backend)
                const errorMessage = result.error || `Error: ${response.status} ${response.statusText}`;
                setMessages(prevMessages => [...prevMessages, { text: `Error: ${errorMessage}`, sender: 'bot' }]);
                return;
            }

            // Check for authorization URL from backend
            if (result.authorization_url) {
                const authLink = <a href={result.authorization_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">Click here to authorize Google Calendar</a>;
                setMessages(prevMessages => [...prevMessages, { text: result.response, sender: 'bot' }, { text: authLink, sender: 'bot' }]);
            } else {
                setMessages(prevMessages => [...prevMessages, { text: result.response, sender: 'bot' }]);
            }

        } catch (error) {
            console.error(error.message);
            setMessages(prevMessages => [...prevMessages, { text: `Network Error: ${error.message}`, sender: 'bot' }]);
        }
    };

    const handleSendMessage = () => {
        if (input.trim()) {
            setMessages([...messages, { text: input, sender: 'user' }]);
            sendMessageToApi(input);
            setInput('');
        }
    };

    const recognition = new webkitSpeechRecognition();

    recognition.onstart = function() {
        console.log('Speech recognition service has started');
    };

    recognition.onend = async function() {
        console.log('Speech recognition service disconnected');
    };

    recognition.onresult = async function(event) {
        const transcript = event.results[0][0].transcript;
        console.log('Result received: ' + transcript);
        setMessages(prevMessages => [...prevMessages, { text: transcript, sender: 'user' }]);
        sendMessageToApi(transcript);
    };

    function toggleStart () {
        console.log("running")
        if(!started){
            recognition.start();
            setStarted(true); 
        }
        else{
            recognition.stop();
            setStarted(false);
        }

    }

    // Check browser support
    if (!('webkitSpeechRecognition' in window)) {
        alert('Sorry, your browser doesn\'t support speech recognition. Try Chrome on desktop/Android.');
    }

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-grow p-4 overflow-y-auto">
        
        <p className="mt-2 text-lg"></p>

        {/* Chat UI */}
        <div className="mt-8 border rounded-lg p-4 h-96 flex flex-col">
          <div className="flex-grow overflow-y-auto mb-4">
            {messages.map((msg, index) => (
              <div key={index} className={`mb-2 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                <span className={`inline-block p-2 rounded-lg ${msg.sender === 'user' ? 'bg-blue-200' : 'bg-gray-200'}`}>
                  {msg.text}
                </span>
              </div>
            ))}
          </div>
          <div className="flex">
            <input
              type="text"
              className="flex-grow border rounded-l-lg p-2 focus:outline-none"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSendMessage();
                }
              }}
            />
            <button
              className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-r-lg"
              onClick={handleSendMessage}
            >
              Send
            </button>
            <button onClick={toggleStart} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Click for speech recognition
        </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Chat