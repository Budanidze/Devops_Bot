CREATE TABLE IF NOT EXISTS Emails(
    ID SERIAL PRIMARY KEY,
    Email VARCHAR (100) NOT NULL
);

INSERT INTO Emails (Email)
VALUES  ('bot@mail.ru'),
	('bob@gmail.com');

CREATE TABLE IF NOT EXISTS Phones(
    ID SERIAL PRIMARY KEY,
    Phone VARCHAR (100) NOT NULL
);

INSERT INTO Phones (Phone)
VALUES  ('+7 (800) 555-35-35'),
	('89845551553');
