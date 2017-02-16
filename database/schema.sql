drop table trans_live;
drop table trans_static;
drop table avg_live;
drop table avg_static;

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

create table avg_live (
	id integer primary key,
	symbol varchar(10),
	averagePrice float
);

create table avg_static (
	id integer primary key,
	symbol varchar(10),
	averagePrice float
);


