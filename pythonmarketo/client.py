from pythonmarketo.helper.http_lib  import  HttpLib
from pythonmarketo.helper.exceptions import MarketoException
import json
import time

class MarketoClient:    
    host = None
    client_id = None
    client_secret = None
    token = None
    expires_in = None
    valid_until = None
    token_type = None
    scope = None
    last_request_id = None
    API_CALLS_MADE = 0
    API_LIMIT = None
    
    def __init__(self, host, client_id, client_secret, api_limit=None):
        assert(host is not None)
        assert(client_id is not None)
        assert(client_secret is not None)
        self.host = host
        self.client_id = client_id
        self.client_secret = client_secret
        self.API_LIMIT = api_limit

    def execute(self, method, *args, **kargs):
        result = None
        if self.API_LIMIT and self.API_CALLS_MADE >= self.API_LIMIT:
            raise Exception({'message':'API Calls exceded the limit : ' + str(self.API_LIMIT), 'code':'416'})

        '''
            max 10 rechecks
        '''
        for i in range(0,15):
            try:
                method_map={
                    'get_leads':self.get_leads,
                    'get_leads_by_listId':self.get_leads_by_listId,
                    'get_activity_types':self.get_activity_types,
                    'get_lead_activity':self.get_lead_activity,
                    'get_paging_token':self.get_paging_token,
                    'update_lead':self.update_lead,
                    'create_lead':self.create_lead,
                    'get_lead_activity_page':self.get_lead_activity_page,
                    'get_email_content_by_id':self.get_email_content_by_id,
                    'get_email_template_content_by_id':self.get_email_template_content_by_id,
                    'get_email_templates':self.get_email_templates,
                    'create_custom_activity':self.create_custom_activity,
                    'get_lead_changes':self.get_lead_changes,
                    'associate_lead':self.associate_lead,
                    'remove_leads_by_listId':self.remove_leads_by_listId,
                    'create_or_update_lead':self.create_or_update_lead,
                    'request_campaign':self.request_campaign
                }

                result = method_map[method](*args,**kargs) 
                self.API_CALLS_MADE += 1
            except MarketoException as e:
                '''
                601 -> auth token not valid
                602 -> auth token expired
                '''
                if e.code in ['601', '602']:
                   continue   
                else:
                    raise Exception({'message':e.message, 'code':e.code})    
            break        
        return result
    

    def authenticate(self):
        if self.valid_until is not None and\
            self.valid_until > time.time():
            return
        args = { 
            'grant_type' : 'client_credentials', 
            'client_id' : self.client_id,
            'client_secret' : self.client_secret
        }
        data = HttpLib().get("https://" + self.host + "/identity/oauth/token", args)
        if data is None: raise Exception("Empty Response")
        self.token = data['access_token']
        self.token_type = data['token_type']
        self.expires_in = data['expires_in']
        self.valid_until = time.time() + data['expires_in'] 
        self.scope = data['scope']

    
    def get_leads(self, filtr, values = None, fields = []):
        self.authenticate()
        values = values if type(values) is str else ",".join(str(v) for v in values) 

        args = {
            'access_token' : self.token,
            'filterType' : str(filtr),
            'filterValues' : values
        }
        if len(fields) > 0:
            args['fields'] = ",".join(fields)
        data = HttpLib().get("https://" + self.host + "/rest/v1/leads.json", args)
        if data is None: raise Exception("Empty Response")
        self.last_request_id = data['requestId']
        if not data['success'] : raise MarketoException(data['errors'][0]) 
        return data['result']

    def get_email_templates(self, offset, maxreturn, status=None):
        self.authenticate()
        if id is None: raise ValueError("Invalid argument: required argument id is none.")
        args = {
            'access_token' : self.token,
            'offset' : offset,
            'maxreturn' : maxreturn
        }
        if status is not None:
            args['status'] = status
        data = HttpLib().get("https://" + self.host + "/rest/asset/v1/emailTemplates.json", args)
        if data is None: raise Exception("Empty Response")
        self.last_request_id = data['requestId']
        if not data['success'] : raise MarketoException(data['errors'][0]) 
        return data['result']
    
    def get_email_content_by_id(self, id):
        self.authenticate()
        if id is None: raise ValueError("Invalid argument: required argument id is none.")
        args = {
            'access_token' : self.token
        }
        data = HttpLib().get("https://" + self.host + "/rest/asset/v1/email/" + str(id) + "/content", args)
        if data is None: raise Exception("Empty Response")
        self.last_request_id = data['requestId']
        if not data['success'] : raise MarketoException(data['errors'][0]) 
        return data['result']
    
    def get_email_template_content_by_id(self, id, status = None):
        self.authenticate()
        if id is None: raise ValueError("Invalid argument: required argument id is none.")
        args = {
            'access_token' : self.token
        }
        if status is not None:
            args['status'] = status
        data = HttpLib().get("https://" + self.host + "/rest/asset/v1/emailTemplate/" + str(id) + "/content", args)
        if data is None: raise Exception("Empty Response")
        self.last_request_id = data['requestId']
        if not data['success'] : raise MarketoException(data['errors'][0]) 
        return data['result']

    def get_leads_by_listId(self, listId = None , batchSize = None, fields = []):
        self.authenticate()
        args = {
            'access_token' : self.token
        }
        if len(fields) > 0:
            args['fields'] = ",".join(fields)
        if batchSize:
            args['batchSize'] = batchSize   
        result_list = []    
        while True:
            data = HttpLib().get("https://" + self.host + "/rest/v1/list/" + str(listId)+ "/leads.json", args)
            if data is None: raise Exception("Empty Response")
            self.last_request_id = data['requestId']
            if not data['success'] : raise MarketoException(data['errors'][0]) 
            result_list.extend(data['result'])
            if len(data['result']) == 0 or 'nextPageToken' not in data:
                break
            args['nextPageToken'] = data['nextPageToken']         
        return result_list    

    def get_activity_types(self):
        self.authenticate()
        args = {
            'access_token' : self.token 
        }
        data = HttpLib().get("https://" + self.host + "/rest/v1/activities/types.json", args)
        if data is None: raise Exception("Empty Response")
        if not data['success'] : raise MarketoException(data['errors'][0]) 
        return data['result']

        
    def get_lead_activity_page(self, activityTypeIds, nextPageToken, batchSize = None, listId = None,  leadIds = None):
        self.authenticate()
        activityTypeIds = activityTypeIds.split() if type(activityTypeIds) is str else activityTypeIds
        leadIds = leadIds.split() if type(leadIds) is str else leadIds
        
        args = {
            'access_token' : self.token,
            'activityTypeIds' : ",".join(activityTypeIds),
            'nextPageToken' : nextPageToken
        }
        if listId:
            args['listId'] = listId
            
        if leadIds:
            args['leadIds'] = leadIds
        
        if batchSize:
            args['batchSize'] = batchSize
            
        data = HttpLib().get("https://" + self.host + "/rest/v1/activities.json", args)
        if data is None: raise Exception("Empty Response")
        if not data['success'] : raise MarketoException(data['errors'][0])
        return data

    def get_lead_activity(self, activityTypeIds, sinceDatetime, batchSize = None, listId = None, leadIds = None):
        activity_result_list = []
        nextPageToken = self.get_paging_token(sinceDatetime = sinceDatetime)
        moreResult = True
        while moreResult:
            result = self.get_lead_activity_page(activityTypeIds, nextPageToken, batchSize, listId, leadIds)
            if result is None:
                break
            moreResult = result['moreResult']
            nextPageToken = result['nextPageToken']
            if 'result' in result:
                activity_result_list.extend(result['result'])
       
        return activity_result_list         
           
    def get_paging_token(self, sinceDatetime):
        self.authenticate()
        args = {
            'access_token' : self.token, 
            'sinceDatetime' : sinceDatetime
        }
        data = HttpLib().get("https://" + self.host + "/rest/v1/activities/pagingtoken.json", args)
        if data is None: raise Exception("Empty Response")
        if not data['success'] : raise MarketoException(data['errors'][0])
        return data['nextPageToken']

    def update_lead(self, lookupField, lookupValue, values):
        updated_lead = dict(list({lookupField : lookupValue}.items()) + list(values.items()))
        data = {
            'action' : 'updateOnly',
            'lookupField' : lookupField,
            'input' : [
             updated_lead
            ]
        }
        return self.post(data)

    def create_lead(self, lookupField, lookupValue, values):
        new_lead = dict(list({lookupField : lookupValue}.items()) + list(values.items()))
        data = {
            'action' : 'createOnly',
            'lookupField' : lookupField,
            'input' : [
             new_lead
            ]
        }
        return self.post(data)
    
    def create_or_update_lead(self, lookupField,  values):
        #new_lead = dict(list({lookupField : 'Email'}.items()) + list(values.items()))
        data = {
            'action' : 'createOrUpdate',
            'lookupField' : lookupField,
            'input' : values
        }
        return self.post(data)
    
    def create_custom_activity(self, body, attributes):
        
        attributes_list = []
        for k,v in attributes.items():
            dict = {'name':k,'value':v}
            attributes_list.append(dict)
        #test
        body['attributes'] = attributes_list
        
        data = {
            'input' :[body]
        }
        return self.post_custom(data)

           
    def post(self, data):
        self.authenticate()
        args = {
            'access_token' : self.token 
        }
        data = HttpLib().post("https://" + self.host + "/rest/v1/leads.json" , args, data)
        if not data['success'] : raise MarketoException(data['errors'][0])
        return data['result']
    
    def post_custom(self, data):
        self.authenticate()
        args = {
            'access_token' : self.token 
        }
        data = HttpLib().post("https://" + self.host + "/rest/v1/activities/external.json" , args, data)
        if not data['success'] : raise MarketoException(data['errors'][0])
        return data['result']
        
    def remove_leads_by_listId(self, listId = None , batchSize = None, ids = []):
        self.authenticate()
        
        ids = ids.split() if type(ids) is str else ",".join(str(v) for v in ids) 
        
        args = {
            'access_token' : self.token,
            'listId' : listId,
            'id' : ids,
            '_method': 'DELETE'
        }
        
        if batchSize:
            args['batchSize'] = batchSize   
        result_list = []    
        while True:
            data = HttpLib().post("https://" + self.host + "/rest/v1/lists/" + str(listId)+ "/leads.json", args)
            if data is None: raise Exception("Empty Response")
            self.last_request_id = data['requestId']
            if not data['success'] : raise MarketoException(data['errors'][0]) 
            result_list.extend(data['result'])
            if len(data['result']) == 0 or 'nextPageToken' not in data:
                break
            args['nextPageToken'] = data['nextPageToken']         
        return result_list
    
    def get_lead_changes(self,  sinceDatetime, fields = None, batchSize = None, listId = None):
            activity_result_list = []
            nextPageToken = self.get_paging_token(sinceDatetime = sinceDatetime)
            moreResult = True
            while moreResult:
                result = self.get_lead_changes_page( nextPageToken, fields, batchSize, listId)
                if result is None:
                    break
                moreResult = result['moreResult']
                nextPageToken = result['nextPageToken']
                if 'result' in result:
                    activity_result_list.extend(result['result'])
            
            return activity_result_list
        
    def get_lead_changes_page(self, nextPageToken, fields= None, batchSize = None, listId = None):
        self.authenticate()
        fields = fields.split() if type(fields) is str else fields
        args = {
            'access_token' : self.token,
            'fields' : ",".join(fields),
            'nextPageToken' : nextPageToken
        }
        if listId:
            args['listId'] = listId
        if batchSize:
            args['batchSize'] = batchSize
        data = HttpLib().get("https://" + self.host + "/rest/v1/activities/leadchanges.json", args)
        if data is None: raise Exception("Empty Response")
        if not data['success'] : raise MarketoException(data['errors'][0])
        return data
    
    def associate_lead(self, lead_id ,cookie):
        self.authenticate()
        args = {
            'access_token' : self.token,
            'cookie':cookie
        }
        data = HttpLib().post("https://" + self.host + "/rest/v1/leads/"+ str(lead_id) + "/associate.json" , args)
        if not data['success'] : raise MarketoException(data['errors'][0])
        return data
    
    def request_campaign(self, id, leads, tokens=None):
        self.authenticate()
        if id is None: raise ValueError("Invalid argument: required argument id is none.")
        if leads is None: raise ValueError("Invalid argument: required argument leads is none.")
        leads_list = [{'id':items} for items in leads]
        if tokens is not None:
            token_list = [{'name':'{{' + k + '}}', 'value':v} for k, v in tokens.items()]
            data={
              'input': {"leads":
                        leads_list,
                        "tokens":
                        token_list
                       }
                 }
        else:
            data={
              'input': {"leads":
                        leads_list
                       }
                 }
        args = {
            'access_token' : self.token
        }
        result = HttpLib().post("https://" + self.host + "/rest/v1/campaigns/" + str(id)+ "/trigger.json", args, data)
        if not result['success'] : raise MarketoException(result['errors'][0])
        return result['success']
        
        
     