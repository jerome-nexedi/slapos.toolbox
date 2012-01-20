##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

__all__ = ['Base', 'Component', 'Entry']

Base = declarative_base()

class Component(Base):
  __tablename__ = 'components'

  id = Column(Integer, primary_key=True)
  title = Column(String, unique=True, nullable=False)
  entries = relationship('Entry', backref='component')

class Entry(Base):
  __tablename__ = 'entries'

  id = Column(Integer, primary_key=True)
  component_id = Column(Integer, ForeignKey('components.id',
                                            onupdate="cascade",
                                            ondelete="cascade"),
                        nullable=False)
  datetime = Column(DateTime, nullable=False)
  title = Column(String, nullable=False)
  content = Column(Text, nullable=True)

class Config(Base):
  __tablename__ = 'configuration_values'

  id = Column(String, nullable=False, unique=True, primary_key=True)
  value = Column(Text, nullable=False)

class Peer(Base):
  __tablename__ = 'peer_tree'

  id = Column(String, nullable=False, unique=True, primary_key=True)
  url = Column(String, nullable=False)
