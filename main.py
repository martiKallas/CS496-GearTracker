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
    attached_to = ndb.StringProperty()

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
        new_weapon.attachment = None
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
        new_attachment.attached_to = None
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
                self.response.write(json.dumps(attachment_dict, indent=4, separators=(',', ': ')))
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
            req = json.loads(self.request.body)
            if 'name' in req:
                attachment.name = req['name']
            if 'primaryAttribute' in req:
                attachment.primaryAttribute = req['primaryAttribute']
            if 'primaryValue' in req:
                attachment.primaryValue = req['primaryValue']
            if 'secondaryAttribute' in req:
                attachment.secondaryAttribute = req['secondaryAttribute']
            if 'secondaryValue' in req:
                attachment.secondaryValue = req['secondaryValue']
            if 'attached_to' in req:
                #remove attachment 
                if req['attached_to'] == None:
                    #attachment is currently attached
                    if attachment.attached_to != None:
                        weapon = ndb.Key(urlsafe = attachment.attached_to).get()
                        if weapon != None:
                            attachment.attached_to = None
                            weapon.attachment = None
                            weapon.put()
                            attachment.put()
                            self.response.status = 204
                            self.response.write("Attachment removed and updated")
                        else:
                            #if could not find weapon, update attachment to be un-attached
                            attachment.attached_to = None
                            attachment.put()
                            self.response.status = 204
                            self.response.write("Could not find weapon - attachment updated")
                    #attachment already un-attached
                    else:
                        attachment.put()
                        self.response.status = 204
                        self.response.write("Attachment was not attached - attachment updated")
                #attach attachment
                else:
                    weapon = ndb.Key(urlsafe = req['attached_to']).get()
                    if weapon == None:
                        self.response.status = 403
                        self.response.write("Could not find specified weapon")
                        return
                    #if attachment is currently attached, remove from old weapon
                    if attachment.attached_to != None:
                        curWeapon = ndb.Key(urlsafe = attachment.attached_to).get()
                        if curWeapon != None:
                            curWeapon.attachment = None
                            curWeapon.put()
                            attachment.attached_to = None
                    #new weapon does not have attachment
                    if weapon.attachment == None:
                        weapon.attachment = attachment.key.urlsafe()
                        attachment.attached_to = weapon.key.urlsafe()
                        weapon.put()
                        attachment.put()
                        self.response.status = 204
                        self.response.write("Weapon attached and updated")
                    #if new weapon has attachment
                    else:
                        curAttachment = ndb.Key(urlsafe = weapon.attachment).get()
                        #set current attachment to free
                        if curAttachment != None:
                            curAttachment.attached_to = None
                            curAttachment.put()
                        attachment.attached_to = weapon.key.urlsafe()
                        weapon.attachment = attachment.key.urlsafe()
                        weapon.put()
                        attachment.put()
                        self.response.status = 204
                        self.response.write("Old attachment removed - attachment updated")
            else:
                attachment.put()
                self.response.status = 204
                self.response.write("Attachment updated")
        else:
            self.response.status = 403
            self.response.write("No attachment id supplied")

   def delete(self, id=None):
        if id:
            attachment = ndb.Key(urlsafe = id).get()
            if attachment:
                #if attachment is attached to a weapon - remove it
                if attachment.attached_to != None:
                    weapon = ndb.Key(urlsafe = attachment.attached_to).get()
                    if weapon != None:
                        weapon.attachment = None
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
                self.response.write(json.dumps(weapon_dict, indent=4, separators=(',', ': ')))
            else:
                self.response.status = 403
                self.response.write("No weapon found")
        else:
            self.response.status = 400
            self.response.write("No id supplied")

   def put(self, id=None):
        if id:
            weapon = ndb.Key(urlsafe = id).get()
            if weapon == None:
                self.response.status = 400
                self.response.write("No weapon found")
                return
            req = json.loads(self.request.body)
            if 'name' in req:
                weapon.name = req['name']
            if 'damage' in req:
                weapon.damage = req['damage']
            if 'attribute' in req:
                weapon.attribute = req['attribute']
            if 'firstTalent' in req:
                weapon.firstTalent = req['firstTalent']
            if 'secondTalent' in req:
                weapon.secondTalent = req['secondTalent']
            if 'freeTalent' in req:
                weapon.freeTalent = req['freeTalent']
            #update weapon attachment
            if 'attachment' in req:
                #remove attachment 
                if req['attachment'] == None:
                    #weapon is currently attached
                    if weapon.attachment != None:
                        attachTemp = ndb.Key(urlsafe = weapon.attachment).get()
                        if attachTemp != None:
                            weapon.attachment = None
                            attachTemp.attached_to = None
                            attachTemp.put()
                            weapon.put()
                            self.response.status = 204
                            self.response.write("Attachment removed and updated")
                        else:
                            #if could not find attachTemp, update weapon to be un-attached
                            weapon.attachment = None
                            weapon.put()
                            self.response.status = 204
                            self.response.write("Could not find attachTemp - weapon updated")
                    #weapon already un-attached
                    else:
                        #add other updates
                        weapon.put()
                        self.response.status = 204
                        self.response.write("Attachment was not attached - weapon updated")
                #add new attachment
                else:
                    newAttach = ndb.Key(urlsafe = req['attachment']).get()
                    if newAttach == None:
                        self.response.status = 403
                        self.response.write("Could not find specified attachment")
                        return
                    #if weapon has attachment, remove old
                    if weapon.attachment != None:
                        curAttach = ndb.Key(urlsafe = weapon.attachment).get()
                        if curAttach != None:
                            curAttach.attached_to = None
                            curAttach.put()
                            weapon.attachment = None
                    #new attachment is not currently on a weapon
                    if newAttach.attached_to == None:
                        newAttach.attached_to = weapon.key.urlsafe()
                        weapon.attachment = newAttach.key.urlsafe()
                        newAttach.put()
                        weapon.put()
                        self.response.status = 204
                        self.response.write("Attachment added and weapon updated")
                    #new attachment is already attached to a weapon
                    else:
                        curWeapon = ndb.Key(urlsafe = newAttach.attached_to).get()
                        #set current weapon to free
                        if curWeapon != None:
                            curWeapon.attachment = None
                            curWeapon.put()
                        weapon.attachment = newAttach.key.urlsafe()
                        newAttach.attached_to = weapon.key.urlsafe()
                        newAttach.put()
                        weapon.put()
                        self.response.status = 204
                        self.response.write("New attachment removed from old weapon and added to current")
            else:
                weapon.put()
                self.response.status = 204
                self.response.write("Weapon updated")
        else:
            self.response.status = 403
            self.response.write("No weapon id supplied")

   def delete(self, id=None):
        if id:
            weapon = ndb.Key(urlsafe = id).get()
            if weapon:
                if weapon.attachment:
                    attachment = ndb.Key(urlsafe = weapon.attachment).get()
                    #if weapon has attachment - remove it
                    if attachment != None:
                        attachment.attached_to = None
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

