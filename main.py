#Sources: 
    # Marti Kallas CS496 - Marina: https://github.com/martiKallas/CS496-Marina
import webapp2
import json
import datetime
from google.appengine.ext import ndb
import logging

##########       HELPER     ########## 

##########       OBJECTS     ########## 
class Weapon(ndb.Model):
    name = ndb.StringProperty()
    damage = ndb.IntegerProperty()
    attribute = ndb.IntegerProperty()
    firstTalent = ndb.StringProperty()
    secondTalent = ndb.StringProperty()
    freeTalent = ndb.StringProperty()
    attachment = ndb.StringProperty()

class Attachment(ndb.Model):
    name = ndb.StringProperty()
    primaryAttribute = ndb.StringProperty()
    primaryValue = ndb.IntegerProperty()
    secondaryAttribute = ndb.StringProperty()
    secondaryValue = ndb.IntegerProperty()

##########       ROUTES     ########## 
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Welcome to the Gear Tracker!')

class Weapons(webapp2.RequestHandler):
    def get(self):
        #source: https://cloud.google.com/appengine/doc:/standard/python/ndb/queryclass
        qry = Weapon.query()
        outString = "["
        for weapon in qry:
            weapon_dict = weapon.to_dict()
            weapon_dict['self'] = '/weapons/' + weapon.key.urlsafe()
            weapon_dict['id'] = weapon.key.urlsafe()
            outString = outString + json.dumps(weapon_dict, indent=4, separators=(',', ': ')) + ',\n'
        if qry.get():
            outString = outString[:-2]
        outString = outString + ']'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outString)


    def post(self):
        req = json.loads(self.request.body)
        new_weapon = Weapon(name=req['name'], damage=req['damage'], attribute=req['attribute'], 
                            firstTalent=req['firstTalent'], secondTalent=req['secondTalent'], 
                            freeTalent=req['freeTalent'], attachment=None)
        new_weapon.put()
        weapon_dict = new_weapon.to_dict()
        weapon_dict['self'] = '/weapons/' + new_weapon.key.urlsafe()
        weapon_dict['id'] = new_weapon.key.urlsafe()
        self.response.write(json.dumps(weapon_dict, indent=4, separators=(',', ': ')))

class Attachments(webapp2.RequestHandler):
    def get(self):
        #source: https://cloud.google.com/appengine/docs/standard/python/ndb/queryclass
        qry = Attachment.query()
        outString = "["
        for attachment in qry:
            attachment_dict = attachment.to_dict()
            attachment_dict['self'] = '/attachments/' + attachment.key.urlsafe()
            attachment_dict['id'] = attachment.key.urlsafe()
            outString = outString + json.dumps(attachment_dict, indent=4, separators=(',', ': ')) + ',\n'
        if qry.get():
            outString = outString[:-2]
        outString = outString + ']'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(outString)

    def post(self):
        req = json.loads(self.request.body)
        new_attachment = Attachment(name=req['name'], primaryAttribute=req['primaryAttribute'], 
                                    primaryValue=req['primaryValue'], secondaryAttribute=req['secondaryAttribute'],
                                    secondaryValue=req['secondaryValue'])
        new_attachment.put()
        attachment_dict = new_attachment.to_dict()
        attachment_dict['self'] = '/attachments/' + new_attachment.key.urlsafe()
        attachment_dict['id'] = new_attachment.key.urlsafe()
        self.response.write(json.dumps(attachment_dict, indent=4, separators=(',', ': ')))

class AttachmentHandler(webapp2.RequestHandler):
   def get(self, id=None):
        if id:
            attachment = ndb.Key(urlsafe = id).get()
            if attachment:
                attachment_dict = attachment.to_dict()
                attachment_dict['self'] = '/attachments/' + id
                attachment_dict['id'] = id
                self.response.write(json.dumps(attachment_dict, default = dateConverter))
            else:
                self.response.status = 403
                self.response.write("No attachment found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def put(self, id=None):
        if id:
            attachment = ndb.Key(urlsafe = id).get()
            if attachment == None:
                self.response.status = 400
                self.response.write("No attachment found")
                return
            bData = json.loads(self.request.body)
            if 'name' in bData:
                attachment.name = bData['name']
            if 'type' in bData:
                attachment.name = bData['type']
            if 'length' in bData:
                attachment.name = bData['length']
            if 'at_sea' in bData:
                #send attachment to sea
                if bData['at_sea'] == True:
                    #attachment is docked
                    if attachment.at_sea == False:
                        weapon = ndb.Key(urlsafe = attachment.weaponID).get()
                        if weapon != None:
                            attachment.at_sea = True
                            attachment.weaponID = None
                            weapon.current_attachment = None
                            weapon.put()
                            attachment.put()
                            self.response.status = 204
                            self.response.write("Attachment now at sea")
                        else:
                            self.response.status = 403
                            self.response.write("Could not find weapon")
                    #attachment already at sea
                    else:
                        self.response.status = 403
                        self.response.write("Attachment already at sea")
                #dock attachment
                else:
                    if 'weaponID' in bData:
                        if attachment.at_sea == True:
                            weapon = ndb.Key(urlsafe = bData['weaponID']).get()
                            if weapon == None:
                                self.response.status = 403
                                self.response.write("No weapon found")
                            elif weapon.current_attachment != None:
                                self.response.status = 403
                                self.response.write("Weapon is occupied")
                            else:
                                weapon.current_attachment = attachment.key.urlsafe()
                                attachment.weaponID = weapon.key.urlsafe()
                                attachment.at_sea = False
                                weapon.put()
                                attachment.put()
                                self.response.status = 204
                                self.response.write("Attachment docked")
                        #attachment already docked
                        else:
                            self.response.status = 403
                            self.response.write("Attachment already docked")
                    #no weaponID supplied
                    else:
                        self.response.status = 400
                        self.response.write("No weapon found to dock at")
            elif 'weaponID' in bData:
                if attachment.at_sea == False:
                    self.response.status = 403
                    self.response.write("Attachment is already docked")
                #attachment already at sea
                else:
                    weapon = ndb.Key(urlsafe = bData['weaponID']).get()
                    if weapon == None:
                        self.response.status = 403
                        self.response.write("No weapon found")
                    elif weapon.current_attachment != None:
                        self.response.status = 403
                        self.response.write("Weapon is occupied")
                    else:
                        weapon.current_attachment = attachment.key.urlsafe()
                        attachment.weaponID = weapon.key.urlsafe()
                        attachment.at_sea = False
                        weapon.put()
                        attachment.put()
                        self.response.status = 204
                        self.response.write("Attachment docked")
            else:
                attachment.put()
                self.response.status = 204
                self.response.write("Attachment updated")
        else:
            self.response.status = 403
            self.response.write("No attachment found")

   def delete(self, id=None):
        if id:
            attachment = ndb.Key(urlsafe = id).get()
            if attachment:
                weapon = None
                if attachment.weaponID != None:
                    weapon = ndb.Key(urlsafe = attachment.weaponID).get()
                if weapon != None:
                    weapon.current_attachment = None
                    weapon.put()
                attachment.key.delete()
                self.response.status = 204
                self.response.write("Attachment Removed")
            else:
                self.response.status = 403
                self.response.write("No attachment found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

class WeaponHandler(webapp2.RequestHandler):
   def get(self, id=None):
        if id:
            weapon = ndb.Key(urlsafe = id).get()
            if weapon:
                weapon_dict = weapon.to_dict()
                weapon_dict['self'] = '/weapons/' + id
                weapon_dict['id'] = id
                self.response.write(json.dumps(weapon_dict, default = dateConverter))
            else:
                self.response.status = 403
                self.response.write("No weapon found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def put(self, id=None):
        if id:
            weapon = ndb.Key(urlsafe = id).get()
            sData = json.loads(self.request.body)
            if 'arrival_date' in sData:
                dateObj = datetime.date.strptime(sData['arrival_date'], '%Y-%m-%d')
                weapon.arrival_date = dateObj
            if 'current_attachment' in sData:
                attachment = ndb.Key(urlsafe = sData['current_attachment']).get()
                if attachment == None:
                    self.response.status = 403
                    self.response.write("No attachment found")
                elif weapon.current_attachment != None:
                    self.response.status = 403
                    self.response.write("Another attachment already docked at weapon")
                elif attachment.at_sea == False:
                    self.response.status = 403
                    self.response.write("Attachment already docked")
                else:
                    weapon.current_attachment = sData['current_attachment']
                    attachment.weaponID = weapon.key.urlsafe()
                    attachment.at_sea = False
                    weapon.arrival_date = datetime.date.today()
                    weapon.put()
                    attachment.put()
                    self.response.status = 204
                    self.response.write("Attachment docked")
            else:
                self.response.status = 204
                self.response.write("Arrival date updated")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def delete(self, id=None):
        if id:
            weapon = ndb.Key(urlsafe = id).get()
            if weapon:
                attachment = ndb.Key(urlsafe = weapon.current_attachment).get()
                if attachment != None:
                    attachment.at_sea = True
                    attachment.weaponID = None
                    attachment.put()
                weapon.key.delete()
                self.response.status = 204
                self.response.write("Weapon Removed")
            else:
                self.response.status = 403
                self.response.write("No weapon found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

        
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/weapons', Weapons),
    ('/weapons/(.*)', WeaponHandler),
    ('/attachments', Attachments),
    ('/attachments/(.*)', AttachmentHandler),
], debug=True)

