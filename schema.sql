/*
Schema for database
May notice lack of relations, foreign keys, etc
This is because although the same attributes are in some tables, they are quite dynamix and connecting them would hinder progress more than anything
*/
drop table trans_live;
drop table trans_static;
drop table averages_live;
drop table averages_static;
drop table anomalies_live;
drop table anomalies_static;

create table trans_live (
	id integer primary key,
	time varchar(30),
	buyer varchar(50),
	seller varchar(50),
	price float,
	volume integer,
	currency varchar(10),
	symbol varchar(10),
	sector varchar(30),
	bidPrice float,
	askPrice float
);

create table trans_static (
	id integer primary key,
	time varchar(30),
	buyer varchar(50),
	seller varchar(50),
	price float,
	volume integer,
	currency varchar(10),
	symbol varchar(10),
	sector varchar(30),
	bidPrice float,
	askPrice float
);

create table anomalies_live (
	id integer primary key,
	tradeid integer UNIQUE,
	category integer,
	actiontaken integer DEFAULT 0, /* whether the anomaly has been dealt with */
	FOREIGN KEY(tradeid) REFERENCES trans_live(id) ON DELETE CASCADE
);
-- I know you said in file we don't need this, but by having it it solves and possible problems
create table anomalies_static (
	id integer primary key,
	tradeid integer UNIQUE,
	category integer,
	actiontaken integer DEFAULT 0, /* whether the anomaly has been dealt with */
	FOREIGN KEY(tradeid) REFERENCES trans_live(id) ON DELETE CASCADE
);

-- Tables for averages
create table averages_live (
	symbol varchar(10),
	averagePrice float,
	averageVolume float,
	numTrades integer
);

create table averages_static (
	symbol varchar(10),
	averagePrice float,
	averageVolume float,
	numTrades integer
);
