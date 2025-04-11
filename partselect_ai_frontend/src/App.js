import React from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  return (
    <div className="App">
      <header className="heading">
        <div className="brand-left">
        <img src="https://partselectcom-gtcdcddbene3cpes.z01.azurefd.net/images/ps-25-year-logo.svg" alt="PartSelect Logo" className="logo" />
          <span>Appliance Parts Assistant</span>
        </div>
        <a
          href="https://www.partselect.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="external-link"
        >
          Visit PartSelect.com
        </a>
      </header>
      <ChatWindow />
    </div>
  );
}

export default App;
