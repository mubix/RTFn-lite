import sqlite3 as lite
import os, time

class DB(object):
    __link = None
    def __init__(self, elite):
        self.elite = elite
        self.connect()
        
    def __exit__(self):
        if not self.__link == None:
            self.__link.close()
            
    def connect(self):
        if not self.__link == None:
            return
        if not os.path.exists("var/rtfn.db"):
            self.create_tables()
        self.__link = lite.connect("var/rtfn.db", check_same_thread=False)
        self.__cur = self.__link.cursor()
        pass 
    
    def commit(self):
        self.__link.commit()
    
    def create_tables(self):
        link = lite.connect("var/rtfn.db")
        cur = link.cursor()
        cur.execute("create table IF NOT EXISTS competitions( \
            c_id INTEGER Primary Key, \
            name TEXT unique, \
            key TEXT NOT NULL unique, \
            start DATETIME Default CURRENT_TIMESTAMP, \
            end DATETIME Default CURRENT_TIMESTAMP \
        ) ")
        cur.execute("create table IF NOT EXISTS users( \
            u_id INTEGER PRIMARY KEY, \
            name TEXT unique, \
            status INTEGER Default 0, \
            register DATETIME Default CURRENT_TIMESTAMP \
        )")
        cur.execute("create table IF NOT EXISTS user_competition( \
            c_id Integer, \
            u_id Integer, \
            FOREIGN KEY(c_id) REFERENCES competitions(c_id), \
            FOREIGN KEY(u_id) REFERENCES users(u_id) \
        )")
        link.commit()
        link.close()
        pass
     
    def create_user(self, user):
        self.connect()
        self.__cur.execute("insert into users (`name`) values (?)", (user,))
        uid= self.elite.createAuthorIfNotExistsFor(user, name=user)
        self.commit()
        return {"db": [self.__cur.lastrowid], "uid": uid["data"]["authorID"] if uid is not None else None}
        pass
    
    def create_competition(self, name, key, add_elite=True):
        self.connect()
        self.__cur.execute("insert into competitions (`name`, `key`) values(?, ?)", (name, key))
        self.commit()
        if not add_elite:
            return True
        gid= self.elite.createGroupIfNotExistsFor(key)
        return {"db": [self.__cur.lastrowid], "gid": gid["data"]["groupID"] if gid is not None else None}
        pass
    
    def user_in_competition(self, user, key):
        self.connect()
        result = self.__cur.execute("select users.u_id from users, competitions, user_competition \
            where users.u_id=user_competition.u_id and competitions.c_id=user_competition.c_id and users.name=? and competitions.key=?", (user, key))
        if not result.fetchone() == None:
            return True
        if self.is_admin(user):
            self.add_user_competition(user, key)
            return True
        return False
        pass
    
    def add_user_competition(self, user, key):
        self.connect()
        if self.user_in_competition(user, key) or self.get_user(user) == None or self.get_competition_from_key(key) == None:
            return False
        self.__cur.execute("insert into user_competition (`c_id`, `u_id`) select u_id, c_id \
            from users, competitions \
            where users.name=? and competitions.key=?", (user, key))
        #self.elite.createGroupIfNotExistsFor(key)
        self.commit()
        return True
    
    def get_user(self, user):
        self.connect()
        result = self.__cur.execute("select u_id, status from users where name=?", (user,))
        uid = self.elite.createAuthorIfNotExistsFor(user)
        return {"db": result.fetchone(), "uid": uid["data"]["authorID"] if uid is not None else None}
    
    def get_competition(self, competition):
        self.connect()
        result = self.__cur.execute("select c_id, key from competitions where name=?", (competition,))
        return result.fetchone()
        pass
    
    def get_competition_from_key(self, key):
        self.connect()
        result = self.__cur.execute("select c_id, name, key from competitions where key=?", (key,))
        gid= self.elite.createGroupIfNotExistsFor(key)
        return {"db": result.fetchone(), "gid": gid["data"]["groupID"] if gid is not None else None}
    
    def make_admin(self, user):
        self.connect()
        if self.get_user(user) == None:
            return False
        self.__cur.execute("update users set status=1 where name=?", (user,))
        self.commit()
        return True
        pass
    
    def is_admin(self, user):
        result = self.__cur.execute("select u_id from users where name=? and status>0", (user,))
        return not result.fetchone() == None
