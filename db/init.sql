CREATE DATABASE qanda;
use qanda;

CREATE TABLE qanda (
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
tag VARCHAR(50) NOT NULL, 
question VARCHAR(2000) NOT NULL, 
answer VARCHAR(2000) NOT NULL,
alternatives VARCHAR(2000) NOT NULL, 
location VARCHAR(255), 
count INT NOT NULL
);

CREATE TABLE user (
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
username VARCHAR(255) NOT NULL,
password VARCHAR(255) NOT NULL,
role VARCHAR(255) NOT NULL
);