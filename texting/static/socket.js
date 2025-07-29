console.log('socket.js loaded');

const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('server_connected', (data) => { // custom event to share data
    console.log('Server says:', data.message);
    // Handle setting online for all the current user's friends logic here
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    // Handle setting offline for all the current user's friends logic here
});

socket.on('send_message', (data) => {
    console.log('Message received:', data);
    // Handle incoming message display logic here
});

socket.on('edit_message', (data) => {
    console.log('Message edited:', data);
    // Handle message edit display logic here
});

socket.on('delete_message', (data) => {
    console.log('Message deleted:', data);
    // Handle message deletion display logic here
});

socket.on('see_message', (data) => {
    console.log('Message seen:', data);
    // Handle message seen display logic here
});

socket.on('joined', (data) => {
    console.log('User joined:', data);
    // Handle user join logic here
});
