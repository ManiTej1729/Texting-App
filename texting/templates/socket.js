const socket = io();
socket.on('connect', () => {
  console.log('Connected to server');
  socket.emit('join', { username: currUser });
});

socket.on('joined', function(data) {
    if (data.status === 'error') {
        console.log(data.message);
    } else if (data.status === 'joined') {
        console.log('Successfully joined!');
    } else if (data.status === 'already joined') {
        console.log('Already joined');
    }
});

socket.on('user_connected', (data) => {
  console.log(`User connected: ${data.username}`);
});

socket.on('user_disconnected', (data) => {
  console.log(`User disconnected: ${data.username}`);
});
