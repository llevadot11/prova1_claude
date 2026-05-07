import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// StrictMode desactivado: causa doble-mount de deck.gl/MapLibre en dev, lo que provoca vibración visual
ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
