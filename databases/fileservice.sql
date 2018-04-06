CREATE USER 'fileservice'@'%' IDENTIFIED BY 'Q9ID8!2nkljadb@n5AEW9V';
CREATE DATABASE fileservice;
GRANT ALL PRIVILEGES ON fileservice.* TO 'fileservice'@'%';
FLUSH PRIVILEGES;