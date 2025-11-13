# AI Agent Frontend

A beautiful React-based chat interface for interacting with the AI Agent backend.

## Features

- 💬 Real-time chat interface
- 🎨 Modern, responsive design
- ⚡ Fast and lightweight
- 🔄 Loading indicators
- 🎯 Message history
- 📱 Mobile-friendly

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

1. Make sure the Python backend server is running on `http://localhost:8000`

2. Start the React development server:
```bash
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

## Building for Production

To create a production build:
```bash
npm run build
```

The build files will be created in the `build` directory.

## Components

- **App.jsx** - Main application component
- **ChatInterface.jsx** - Chat container with state management
- **MessageList.jsx** - Displays chat messages
- **MessageInput.jsx** - Input form for sending messages

## API Configuration

The frontend expects the backend API to be running at `http://localhost:8000/chat`.

To change the API endpoint, modify the fetch URL in `ChatInterface.jsx`:
```javascript
const response = await fetch('YOUR_API_URL', {
  // ...
});
```

## Technologies Used

- React 18
- CSS3 with modern features
- Axios for HTTP requests
- React Hooks for state management
