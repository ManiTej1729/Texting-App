-- For users
create table users ( 
    S_no INT PRIMARY KEY AUTO_INCREMENT, 
    username VARCHAR(255), 
    password VARCHAR(1000)
);

-- For Single user (this is a sample for admin)
create table Admin (
    S_no INT PRIMARY KEY AUTO_INCREMENT, 
    contact_name VARCHAR(255), 
    pending_status VARCHAR(17)
);

-- For last seen
create table lastSeen (
    S_no INT PRIMARY KEY AUTO_INCREMENT, 
    contact_name VARCHAR(255), 
    lastSeenTime VARCHAR(255)
);

CREATE Table `test1@test2` ( 
    S_no INT PRIMARY KEY AUTO_INCREMENT, 
    textBody TEXT, 
    sender VARCHAR(255), 
    receiver VARCHAR(255), 
    msgTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    image LONGBLOB, audio LONGBLOB, 
    msgType VARCHAR(20), 
    msgStatus VARCHAR(20), 
    replyMsg INT DEFAULT 0, -- 0 for not replying to some other message or else it is the S_no of that msg in the same table
    deleteStatus VARCHAR(20), 
    forwardedFlag INT DEFAULT 0
);