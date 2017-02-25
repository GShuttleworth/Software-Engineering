/*
Schema for database
May notice lack of relations, foreign keys, etc
This is because although the same attributes are in some tables, they are quite dynamix and connecting them would hinder progress more than anything
*/
drop table trans_live;
drop table trans_static;
drop table running_price_avg_live;
drop table running_price_avg_static;
drop table daily_price_avg_live;
drop table daily_price_avg_static;
drop table running_volume_avg_live;
drop table running_volume_avg_static;
drop table daily_volume_avg_live;
drop table daily_volume_avg_static;
drop table anomalies_live;

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

-- Tables for prices
create table running_price_avg_live (
	symbol varchar(10),
	averagePrice float
);

create table running_price_avg_static (
	symbol varchar(10),
	averagePrice float
);

create table daily_price_avg_live (
	symbol varchar(10),
	averagePrice float,
	dateRecorded varchar(30)
);

create table daily_price_avg_static (
	symbol varchar(10),
	averagePrice float,
	dateRecorded varchar(30)
);

-- Tables for volume
create table running_volume_avg_live (
	symbol varchar(10),
	averageVolume float
);

create table running_volume_avg_static (
	symbol varchar(10),
	averageVolume float
);

create table daily_volume_avg_live (
	symbol varchar(10),
	averageVolume float,
	dateRecorded varchar(30)
);

create table daily_volume_avg_static (
	symbol varchar(10),
	averageVolume float,
	dateRecorded varchar(30)
);



