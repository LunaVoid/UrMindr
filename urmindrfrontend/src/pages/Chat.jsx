import React from 'react'
import { useState, useEffect } from "react";



function Chat() {

    const [started, setStarted] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    const sendMessageToApi = async (message) => {
        const url = "http://127.0.0.1:5000/api/toolcall";
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: message })
            });
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            const result = await response.json();
            setMessages(prevMessages => [...prevMessages, { text: result.response, sender: 'bot' }]);
        } catch (error) {
            console.error(error.message);
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