#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/3/6
Desc    :
create database chinook DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
/usr/local/bin/mysql -uroot -pxxx chinook < Chinook_MySql_AutoIncrementPKs.sql
pip install sqlacodegen
sqlacodegen mysql://root:windpro@localhost/chinook > chinook_models.py
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Album(db.Model):
    __tablename__ = 'Album'

    AlbumId = Column(Integer, primary_key=True)
    Title = Column(String(160), nullable=False)
    ArtistId = Column(ForeignKey(u'Artist.ArtistId'), nullable=False, index=True)

    Artist = relationship(u'Artist')


class Artist(db.Model):
    __tablename__ = 'Artist'

    ArtistId = Column(Integer, primary_key=True)
    Name = Column(String(120))


class Customer(db.Model):
    __tablename__ = 'Customer'

    CustomerId = Column(Integer, primary_key=True)
    FirstName = Column(String(40), nullable=False)
    LastName = Column(String(20), nullable=False)
    Company = Column(String(80))
    Address = Column(String(70))
    City = Column(String(40))
    State = Column(String(40))
    Country = Column(String(40))
    PostalCode = Column(String(10))
    Phone = Column(String(24))
    Fax = Column(String(24))
    Email = Column(String(60), nullable=False)
    SupportRepId = Column(ForeignKey(u'Employee.EmployeeId'), index=True)

    Employee = relationship(u'Employee')


class Employee(db.Model):
    __tablename__ = 'Employee'

    EmployeeId = Column(Integer, primary_key=True)
    LastName = Column(String(20), nullable=False)
    FirstName = Column(String(20), nullable=False)
    Title = Column(String(30))
    ReportsTo = Column(ForeignKey(u'Employee.EmployeeId'), index=True)
    BirthDate = Column(DateTime)
    HireDate = Column(DateTime)
    Address = Column(String(70))
    City = Column(String(40))
    State = Column(String(40))
    Country = Column(String(40))
    PostalCode = Column(String(10))
    Phone = Column(String(24))
    Fax = Column(String(24))
    Email = Column(String(60))

    parent = relationship(u'Employee', remote_side=[EmployeeId])


class Genre(db.Model):
    __tablename__ = 'Genre'

    GenreId = Column(Integer, primary_key=True)
    Name = Column(String(120))


class Invoice(db.Model):
    __tablename__ = 'Invoice'

    InvoiceId = Column(Integer, primary_key=True)
    CustomerId = Column(ForeignKey(u'Customer.CustomerId'), nullable=False, index=True)
    InvoiceDate = Column(DateTime, nullable=False)
    BillingAddress = Column(String(70))
    BillingCity = Column(String(40))
    BillingState = Column(String(40))
    BillingCountry = Column(String(40))
    BillingPostalCode = Column(String(10))
    Total = Column(Numeric(10, 2), nullable=False)

    Customer = relationship(
        u'Customer',
        backref=backref(
            'Invoices',
            uselist=True,
        )
    )


class InvoiceLine(db.Model):
    __tablename__ = 'InvoiceLine'

    InvoiceLineId = Column(Integer, primary_key=True)
    InvoiceId = Column(ForeignKey(u'Invoice.InvoiceId'), nullable=False, index=True)
    TrackId = Column(ForeignKey(u'Track.TrackId'), nullable=False, index=True)
    UnitPrice = Column(Numeric(10, 2), nullable=False)
    Quantity = Column(Integer, nullable=False)

    Invoice = relationship(u'Invoice')
    Track = relationship(u'Track')


class MediaType(db.Model):
    __tablename__ = 'MediaType'

    MediaTypeId = Column(Integer, primary_key=True)
    Name = Column(String(120))


class Playlist(db.Model):
    __tablename__ = 'Playlist'

    PlaylistId = Column(Integer, primary_key=True)
    Name = Column(String(120))

    Track = relationship(u'Track', secondary='PlaylistTrack')


t_PlaylistTrack = db.Table(
    'PlaylistTrack', db.Model.metadata,
    Column('PlaylistId', ForeignKey(u'Playlist.PlaylistId'), primary_key=True, nullable=False),
    Column('TrackId', ForeignKey(u'Track.TrackId'), primary_key=True, nullable=False, index=True)
)


class Track(db.Model):
    __tablename__ = 'Track'

    TrackId = Column(Integer, primary_key=True)
    Name = Column(String(200), nullable=False)
    AlbumId = Column(ForeignKey(u'Album.AlbumId'), index=True)
    MediaTypeId = Column(ForeignKey(u'MediaType.MediaTypeId'), nullable=False, index=True)
    GenreId = Column(ForeignKey(u'Genre.GenreId'), index=True)
    Composer = Column(String(220))
    Milliseconds = Column(Integer, nullable=False)
    Bytes = Column(Integer)
    UnitPrice = Column(Numeric(10, 2), nullable=False)

    Album = relationship(u'Album')
    Genre = relationship(u'Genre')
    MediaType = relationship(u'MediaType')

    PlaylistCollection = relationship(
        "Playlist",
        secondary=t_PlaylistTrack,
        backref=backref(
            "Tracks",
        )
    )
